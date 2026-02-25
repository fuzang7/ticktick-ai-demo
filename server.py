import os
import sys
import logging
import asyncio
import contextlib
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.server import InitializationOptions

from dida_client import DidaClient

# 使用绝对路径确保 token 文件能正确找到
TOKEN_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".token-oauth")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DidaMCPServer:
    def __init__(self):
        self.dida_client = None
        self._initialized = False

    def _init_client(self):
        if self._initialized:
            return
        try:
            self.dida_client = DidaClient(token_file=TOKEN_FILE_PATH)
            logger.info("DidaClient initialized successfully")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize DidaClient: {e}")
            raise RuntimeError(f"Failed to initialize DidaClient: {e}")

    def ensure_client(self):
        if not self._initialized:
            self._init_client()

    def get_tasks(self, project_id: Optional[str] = None, list_id: Optional[str] = None) -> Any:
        self.ensure_client()
        if project_id:
            return self.dida_client.get_project_tasks(project_id)
        elif list_id:
            return self.dida_client.get_project_tasks(list_id)
        else:
            return self.dida_client.get_active_tasks_from_all_projects()

    def add_task(
        self,
        title: str,
        content: str = "",
        due_date: Optional[str] = None,
        project_id: Optional[str] = None,
        startDate: Optional[str] = None,
        timeZone: Optional[str] = None,
        isAllDay: Optional[bool] = None
    ) -> dict:
        self.ensure_client()
        
        # 规范化日期格式，添加时区信息
        def normalize_date(date_str):
            if not date_str:
                return None
            import re
            # 如果已经有时区，直接返回
            if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}', date_str):
                return date_str
            # 尝试添加时区
            # 格式: 2026-02-25T14:00:00 -> 2026-02-25T14:00:00+08:00
            if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', date_str):
                return date_str + "+08:00"
            # 格式: 2026-02-25 14:00 -> 2026-02-25T14:00:00+08:00
            match = re.match(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})', date_str)
            if match:
                return f"{match.group(1)}-{match.group(2)}-{match.group(3)}T{match.group(4)}:{match.group(5)}:00+08:00"
            return date_str
        
        effective_due_date = normalize_date(due_date)
        effective_start_date = normalize_date(startDate)
        
        # 如果提供了时间参数但没有明确指定isAllDay，自动设为False
        if (effective_start_date or effective_due_date) and isAllDay is None:
            isAllDay = False
            logger.info(f"Auto-set isAllDay=False because startDate or due_date was provided")
            
        logger.info(f"add_task: title={title}, isAllDay={isAllDay}, startDate={effective_start_date}, due_date={effective_due_date}")
        result = self.dida_client.create_task(
            title=title,
            content=content,
            due_date=effective_due_date,
            project_id=project_id,
            start_date=effective_start_date,
            time_zone=timeZone,
            is_all_day=isAllDay if isAllDay is not None else True
        )
        if result is None:
            raise RuntimeError("Failed to create task")
        return result

    def complete_task(self, task_id: str) -> dict:
        self.ensure_client()
        # Try to get task first to get etag, then update with status=2
        # Include necessary fields for the update
        result = self.dida_client.update_task(
            task_id, 
            status=2,
            taskId=task_id
        )
        if result is None:
            raise RuntimeError(f"Failed to complete task {task_id}")
        return result


def create_server():
    server = Server("ticktick-mcp-server")
    dida_server = DidaMCPServer()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="get_tasks",
                description="Get tasks from TickTick. Returns ALL active tasks across all projects if no project_id or list_id specified.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "Project ID to fetch tasks from. If not provided, returns inbox tasks."
                        },
                        "list_id": {
                            "type": "string",
                            "description": "Alternative parameter for project/list ID."
                        }
                    }
                }
            ),
            Tool(
                name="add_task",
                description="Add a new task to TickTick. Note: If you provide startDate or due_date, the task will automatically be created as a non-all-day task.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Task title (required)"
                        },
                        "content": {
                            "type": "string",
                            "description": "Task description/content (optional)"
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Due date in ISO 8601 format, e.g., '2026-02-25T14:00:00+08:00' (optional). If provided with a time, task will be non-all-day."
                        },
                        "project_id": {
                            "type": "string",
                            "description": "Project ID to create task in. If not provided, uses inbox."
                        },
                        "startDate": {
                            "type": "string",
                            "description": "Task start time in ISO 8601 format, e.g., '2026-02-25T14:00:00+08:00' (optional). If provided with a time, task will be non-all-day."
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Alias for startDate. Use this if startDate doesn't work."
                        },
                        "dueDate": {
                            "type": "string",
                            "description": "Alias for due_date. Use this if due_date doesn't work."
                        },
                        "timeZone": {
                            "type": "string",
                            "description": "Time zone for the task, defaults to 'Asia/Shanghai' (optional)"
                        },
                        "isAllDay": {
                            "type": "boolean",
                            "description": "Whether the task is all-day. If not provided but startDate/due_date has time, will auto-set to False"
                        }
                    },
                    "required": ["title"]
                }
            ),
            Tool(
                name="complete_task",
                description="Mark a task as completed.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to mark as completed (required)"
                        }
                    },
                    "required": ["task_id"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        try:
            # 重定向标准输出到 stderr，防止底层 print 破坏 MCP stdio 协议
            with contextlib.redirect_stdout(sys.stderr):
                if name == "get_tasks":
                    # 使用 asyncio.to_thread 包装同步网络调用，防止阻塞事件循环
                    tasks = await asyncio.to_thread(
                        dida_server.get_tasks,
                        arguments.get("project_id"),
                        arguments.get("list_id")
                    )
                    return [TextContent(type="text", text=str(tasks))]

                elif name == "add_task":
                    # 支持多种时间参数名
                    due_date = arguments.get("due_date") or arguments.get("dueDate") or arguments.get("endDate")
                    start_date = arguments.get("startDate") or arguments.get("start_date") or arguments.get("startDateTime")
                    is_all_day = arguments.get("isAllDay") or arguments.get("is_all_day") or arguments.get("isAllDayTask")
                    
                    logger.info(f"call_tool add_task received arguments: {arguments}")
                    logger.info(f"Parsed: due_date={due_date}, start_date={start_date}, is_all_day={is_all_day}")
                    
                    result = await asyncio.to_thread(
                        dida_server.add_task,
                        title=arguments["title"],
                        content=arguments.get("content", ""),
                        due_date=due_date,
                        project_id=arguments.get("project_id"),
                        startDate=start_date,
                        timeZone=arguments.get("timeZone", "Asia/Shanghai"),
                        isAllDay=is_all_day
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "complete_task":
                    result = await asyncio.to_thread(
                        dida_server.complete_task,
                        arguments["task_id"]
                    )
                    return [TextContent(type="text", text=str(result))]

                else:
                    raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    return server


async def main():
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ticktick-mcp-server",
                server_version="1.0.0",
                capabilities={}
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
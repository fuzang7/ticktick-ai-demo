"""AI Project Manager - Integrates TickTick task management with LLM planning.

This application combines TickTick API for task management with LLM capabilities
for intelligent task planning and daily review generation.
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dida_client import DidaClient
from llm_client import LLMClient
from prompt_manager import PromptManager


class DailyLogManager:
    """Manages daily logs for continuous recording and evening summarization.

    This class handles:
    1. Automatic directory creation for logs
    2. Structured JSON log storage with timestamps
    3. Retrieval and formatting of logs for AI analysis
    """

    def __init__(self, logs_dir: str = "logs"):
        """Initialize the log manager with automatic directory creation.

        Args:
            logs_dir: Directory to store log files (default: "logs/").
                     Automatically creates directory if it doesn't exist.

        Raises:
            OSError: If directory creation fails due to permission or disk issues.
        """
        self.logs_dir = logs_dir
        self.ensure_logs_dir()

    def ensure_logs_dir(self) -> bool:
        """Ensure the logs directory exists, creating it if necessary.

        Returns:
            True if directory exists or was created successfully, False otherwise.

        Raises:
            OSError: If directory creation fails due to permission or disk issues.
        """
        try:
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir, exist_ok=True)
                print(f"📁 Created logs directory: {self.logs_dir}")
            return True
        except OSError as e:
            raise OSError(f"Failed to create logs directory '{self.logs_dir}': {e}")

    def get_today_log_file(self) -> str:
        """Get the path to today's log file.

        Returns:
            Absolute path to today's log file (format: logs/YYYYMMDD_stream.json).
        """
        today_str = datetime.now().strftime("%Y%m%d")
        return os.path.join(self.logs_dir, f"{today_str}_stream.json")

    def add_log_entry(self, log_type: str, content: str,
                     ai_response: str = "", auto_timestamp: bool = True) -> bool:
        """Add a log entry to today's log file.

        Args:
            log_type: Type of log entry (e.g., "user_input", "task_completion").
            content: The main content of the log entry.
            ai_response: AI's response (if applicable).
            auto_timestamp: Whether to automatically add current timestamp.

        Returns:
            True if log was successfully written, False otherwise.
        """
        try:
            log_file = self.get_today_log_file()

            # Load existing logs
            logs = self.get_today_logs()

            # Create new log entry
            log_entry = {
                "type": log_type,
                "content": content
            }

            if ai_response:
                log_entry["ai_response"] = ai_response

            if auto_timestamp:
                log_entry["timestamp"] = datetime.now().isoformat()

            # Add to logs and save
            logs.append(log_entry)

            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"❌ Failed to write log entry: {e}")
            return False

    def get_today_logs(self) -> List[Dict[str, str]]:
        """Retrieve all logs from today's log file.

        Returns:
            List of log entries. Returns empty list if file doesn't exist or is invalid.
        """
        try:
            log_file = self.get_today_log_file()

            if not os.path.exists(log_file):
                return []

            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)

            if not isinstance(logs, list):
                return []

            return logs

        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Failed to read log file: {e}")
            return []
        except Exception as e:
            print(f"⚠️  Unexpected error reading logs: {e}")
            return []

    def clear_today_logs(self) -> bool:
        """Clear today's log file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            log_file = self.get_today_log_file()
            if os.path.exists(log_file):
                os.remove(log_file)
                return True
            return True  # Already doesn't exist
        except Exception as e:
            print(f"❌ Failed to clear logs: {e}")
            return False

    def format_logs_for_prompt(self, limit: int = 20) -> str:
        """Format recent logs for inclusion in AI prompts.

        Args:
            limit: Maximum number of recent logs to include.

        Returns:
            Formatted string of recent logs.
        """
        logs = self.get_today_logs()
        if not logs:
            return "今天尚无记录"

        # Get most recent logs (within limit)
        recent_logs = logs[-limit:]

        formatted = []
        for log in recent_logs:
            timestamp = log.get("timestamp", "未知时间")
            log_type = log.get("type", "unknown")
            content = log.get("content", "")
            ai_response = log.get("ai_response", "")

            # Clean up timestamp for display
            if "T" in timestamp:
                timestamp = timestamp.split("T")[1][:5]  # Get only HH:MM

            entry = f"[{timestamp}] {content}"
            if ai_response:
                entry += f" -> {ai_response[:50]}..."

            formatted.append(entry)

        return "\n".join(formatted)

    def get_daily_summary_for_audit(self) -> str:
        """Format all of today's logs for the end-of-day audit.

        Returns:
            Comprehensive formatted string of all today's logs.
        """
        logs = self.get_today_logs()
        if not logs:
            return "今天尚无记录"

        formatted = []
        for i, log in enumerate(logs, 1):
            timestamp = log.get("timestamp", "未知时间")
            log_type = log.get("type", "unknown")
            content = log.get("content", "")
            ai_response = log.get("ai_response", "")

            # Extract time only
            if "T" in timestamp:
                time_part = timestamp.split("T")[1][:8]  # HH:MM:SS
            else:
                time_part = timestamp[:8]

            entry = f"{i:2}. {time_part} [{log_type.upper():10}] {content}"
            if ai_response and ai_response.strip():
                # Indent AI response for readability
                entry += f"\n        AI: {ai_response[:100]}..."

            formatted.append(entry)

        return "\n".join(formatted)


class AIProjectManager:
    """Main application that integrates TickTick task management with AI planning.

    This manager provides multiple core functionalities:
    1. Goal decomposition and task planning with time scheduling
    2. Daily review and progress report generation
    3. Strategic war room for continuous conversation and logging
    4. Global task analysis dashboard

    Attributes:
        dida (DidaClient): TickTick API client
        llm (LLMClient): LLM client for AI planning and analysis
        pm (PromptManager): Centralized prompt manager for AI personas and templates
        log_manager (DailyLogManager): Manager for daily activity logs
    """

    def __init__(self):
        """Initialize the AI Project Manager.

        Raises:
            SystemExit: If initialization fails due to configuration or connection issues.
        """
        # Configure logging for this module only
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        print("[AI] Initializing AI Project Manager...")
        try:
            self.dida = DidaClient()
            self.llm = LLMClient()
            self.pm = PromptManager()
            self.log_manager = DailyLogManager()
            print("✅ System ready! Connected to TickTick & LLM")
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            print("\nPlease check your .env file configuration.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            sys.exit(1)

    def run_planner(self) -> None:
        """Core function 1: Goal decomposition and planning with parent-child tasks.

        This method:
        1. Takes a user goal as input
        2. Uses LLM to decompose it into subtasks with time planning
        3. Creates a parent task in TickTick for the overall goal
        4. Creates subtasks with proper parent-child relationships and due dates
        """
        print("\n" + "=" * 40)
        print("🎯 Intelligent Planning Mode (Planner)")
        print("=" * 40)

        goal = input(
            "\nPlease tell me your main goal (e.g., 'Learn Linux driver development in one week'):\n> "
        ).strip()
        if not goal:
            print("No goal provided, returning to menu.")
            return

        print(f"\n🧠 Thinking about how to decompose '{goal}'...")

        # 1. Use AI for task decomposition with time planning
        try:
            tasks = self._generate_task_plan_with_pm(
                goal,
                context="User wants a gradual, step-by-step approach",
                temperature=0.3  # Low creativity for consistent planning
            )
        except Exception as e:
            print(f"❌ AI planning failed: {e}")
            return

        if not tasks:
            print("❌ No tasks generated. Please try again with a different goal.")
            return

        # 2. Display the proposed plan
        print(f"\n📋 AI Suggested Plan:")
        print(f"   Main Goal: {goal}")
        now = datetime.now()

        for i, task in enumerate(tasks, 1):
            offset = task.get('day_offset', 0)
            plan_date = now + timedelta(days=offset)
            date_str = plan_date.strftime("%b %d")
            print(f"   [{i}] {date_str} | {task['title']}")

        # 3. Get user confirmation
        confirm = input("\n❓ Execute and write to TickTick? (y/n): ").lower().strip()

        if confirm == 'y':
            print("\n🚀 Writing to TickTick...")

            # Create parent task for the overall goal
            parent_task = self.dida.create_task(
                title=f"[Project] {goal}",  # Prefix for clarity
                content="Project task group automatically planned by AI",
                is_all_day=True,
                due_date=now.strftime("%Y-%m-%dT00:00:00+08:00")  # Start today
            )

            if not parent_task:
                print("❌ Parent task creation failed. Process terminated.")
                return

            parent_id = parent_task['id']
            print(f"  ✅ Parent task created: {goal}")

            # Create subtasks with parent-child relationships
            success_count = 0
            for task in tasks:
                offset = task.get('day_offset', 0)
                due_date = now + timedelta(days=offset)
                # Format: ISO 8601 with timezone offset
                due_date_str = due_date.strftime("%Y-%m-%dT00:00:00+08:00")

                result = self.dida.create_task(
                    title=task['title'],
                    content=task['content'],
                    parent_id=parent_id,     # Key: link to parent
                    due_date=due_date_str,   # Key: set due date
                    is_all_day=True
                )

                if result:
                    date_display = due_date.strftime("%b %d")
                    print(f"    └─ ✅ Subtask: {task['title']} ({date_display})")
                    success_count += 1
                else:
                    print(f"    └─ ❌ Failed: {task['title']}")

            print(
                f"\n✨ Complete! Created 1 parent task and {success_count} subtasks in TickTick."
            )
            print(f"   Parent task ID: {parent_id}")
        else:
            print("👌 Operation cancelled.")

    def run_auditor(self) -> None:
        """Core function 2: Daily review and progress report generation with log integration.

        This method:
        1. Retrieves current tasks from TickTick inbox
        2. Optionally reads today's activity logs
        3. Asks user for daily progress report
        4. Uses LLM to generate a structured daily review with full context
        5. Optionally saves the review and integrates with Obsidian
        """
        print("\n" + "=" * 40)
        print("📝 Daily Review Mode (Auditor)")
        print("=" * 40)

        print("📡 Reading inbox task status...")
        try:
            tasks = self.dida.get_inbox_tasks()
        except Exception as e:
            print(f"❌ Failed to retrieve tasks: {e}")
            return

        if not tasks:
            print("⚠️ Inbox is empty, nothing to review.")
            return

        # Note: The TickTick API typically returns only incomplete tasks
        # status values: 0=Normal, 2=Completed (may vary by API version)
        # For simplicity, we assume all retrieved tasks are pending
        task_titles = [t['title'] for t in tasks[:10]]  # Limit to 10 to avoid token overflow
        print(f"\n🔍 Found {len(tasks)} pending tasks in your inbox.")

        user_input = input(
            "\nPlease briefly describe your progress today "
            "(e.g., 'Completed driver compilation but stuck on module loading'):\n> "
        ).strip()

        if not user_input:
            print("No progress description provided.")
            return

        # Check if user wants to include today's logs
        include_logs = input("\n🔍 Include today's activity logs? (y/n): ").lower().strip()
        daily_logs = None

        if include_logs == 'y':
            daily_logs = self.log_manager.get_today_logs()
            if daily_logs:
                print(f"📊 Including {len(daily_logs)} log entries in analysis")
            else:
                print("📊 No logs found for today")

        # Prepare task data for prompt_manager
        # Note: We currently only have pending tasks, so completed is empty
        tasks_data = {
            "completed": [],  # TickTick API typically only returns incomplete tasks
            "pending": task_titles
        }

        # Generate prompt using prompt_manager (now with optional logs)
        print("\n🧠 Generating comprehensive daily report...")
        try:
            user_prompt = self.pm.render_auditor_prompt(
                tasks_data=tasks_data,
                daily_logs=daily_logs,
                user_input=user_input
            )
            system_prompt = self.pm.get_system_prompt()

            report = self.llm.chat(
                user_prompt,
                system_prompt=system_prompt,
                temperature=0.5,  # Balanced creativity for insightful but consistent reports
                max_tokens=500   # Limit length for concise reports
            )
        except Exception as e:
            print(f"❌ Failed to generate report: {e}")
            return

        # Display the report
        print("\n" + "-" * 20 + " Generated Report " + "-" * 20)
        print(report)
        print("-" * 50)

        # Enhanced save options
        print("\n💾 Save options:")
        print("  1. Local file only")
        print("  2. Local file + Obsidian (if configured)")
        print("  3. Don't save")

        save_option = input("\n❓ Select save option (1, 2, or 3): ").strip()

        if save_option in ['1', '2']:
            # Save to local file
            date_str = datetime.now().strftime("%Y-%m-%d")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"DailyReview_{timestamp}.md"

            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"# Daily Review - {date_str}\n\n")
                    f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                    f.write(report)
                print(f"📄 Saved to local file: {filename}")

                # Optionally integrate with Obsidian
                if save_option == '2':
                    obsidian_path = os.getenv("OBSIDIAN_DAILY_PATH")
                    if obsidian_path:
                        try:
                            # Check if file exists, create if not
                            if not os.path.exists(obsidian_path):
                                with open(obsidian_path, "w", encoding="utf-8") as f:
                                    f.write(f"# Daily Note - {date_str}\n\n")

                            # Append report to Obsidian
                            with open(obsidian_path, "a", encoding="utf-8") as f:
                                f.write("\n\n---\n")
                                f.write("# AI Daily Review\n")
                                f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
                                f.write(report)

                            print(f"📝 Appended to Obsidian: {obsidian_path}")
                        except Exception as obsidian_error:
                            print(f"⚠️  Obsidian integration failed: {obsidian_error}")
                    else:
                        print("⚠️  OBSIDIAN_DAILY_PATH not set, skipping Obsidian integration")

            except Exception as e:
                print(f"❌ Failed to save file: {e}")
        else:
            print("👌 Report not saved.")

    def run_dashboard(self) -> None:
        """Core function 3: Global task analysis and health dashboard.

        This method:
        1. Collects all active tasks across all projects
        2. Analyzes task distribution, priorities, and due dates
        3. Uses LLM to generate a comprehensive task management health report
        4. Provides actionable insights and recommendations
        """
        print("\n" + "=" * 40)
        print("📊 AI Global Dashboard")
        print("=" * 40)

        print("\n📡 Collecting task data from all projects...")
        print("This may take a moment as we fetch data from all your projects.")

        try:
            # Step 1: Collect and prepare task data
            dashboard_data = self.dida.prepare_dashboard_data_for_llm(
                max_tasks=50,
                include_content=False  # Exclude content for token efficiency
            )

            if not dashboard_data['analysis_ready']:
                print(f"\n⚠️  {dashboard_data.get('message', 'No data available for analysis')}")
                return

            summary = dashboard_data['summary']
            tasks = dashboard_data['tasks']
            categorization = dashboard_data['categorization']

            # Step 2: Display basic statistics
            print(f"\n📊 Data Collection Complete:")
            print(f"   • Total Active Tasks: {summary['total_active_tasks']}")
            print(f"   • Projects Analyzed: {summary['projects_with_tasks']}")
            print(f"   • Overdue Tasks: {summary.get('overdue_tasks', 0)}")
            print(f"   • High Priority Tasks: {categorization['by_priority'].get('High', 0)}")

            if summary['has_more_tasks']:
                print(f"   • Note: Showing {summary['analysis_task_count']} of {summary['total_active_tasks']} tasks for analysis")

            # Step 3: Prepare data for LLM analysis
            print("\n🧠 Analyzing task management health with AI...")

            # Extract and format task list for prompt_manager
            task_list_str = self._format_task_list_for_dashboard(tasks)

            # Prepare summary for prompt_manager (add missing fields if needed)
            # prompt_manager expects 'high_priority_count' in summary
            summary_for_pm = summary.copy()  # Create a copy to avoid modifying the original
            if 'high_priority_count' not in summary_for_pm:
                # Add high priority count from categorization
                summary_for_pm['high_priority_count'] = categorization['by_priority'].get('High', 0)

            # Generate prompt using prompt_manager
            prompt = self.pm.render_dashboard_prompt(summary_for_pm, task_list_str)

            # Step 4: Generate analysis report
            report = self.llm.chat(
                prompt,
                system_prompt=self.pm.get_system_prompt(),
                temperature=0.4,  # Balanced for analytical tasks
                max_tokens=4000    # Generous but limited for comprehensive analysis
            )

            # Step 5: Display the report
            print("\n" + "=" * 60)
            print("📋 TASK MANAGEMENT HEALTH REPORT")
            print("=" * 60)
            print(report)
            print("=" * 60)

            # Step 6: Offer to save report
            save = input("\n❓ Save this report as Markdown file? (y/n): ").lower().strip()
            if save == 'y':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"TaskDashboard_{timestamp}.md"
                try:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write("# Task Management Health Report\n\n")
                        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                        f.write(report)
                    print(f"✅ Report saved to: {filename}")
                except Exception as e:
                    print(f"❌ Failed to save report: {e}")

        except Exception as e:
            print(f"❌ Dashboard analysis failed: {e}")
            self.logger.error(f"Dashboard error: {e}")

    
    
    def _format_task_list_for_dashboard(self, tasks: List[Dict[str, Any]]) -> str:
        """Format task list for dashboard prompt.

        Formats tasks into a readable string similar to the original
        _build_dashboard_prompt's formatting.

        Args:
            tasks: List of task dictionaries from DidaClient.

        Returns:
            Formatted task list string.
        """
        task_list_str = ""
        for i, task in enumerate(tasks[:30], 1):  # Limit to 30 tasks in prompt
            task_line = f"{i}. [{task['project']}] {task['title']}"
            if task.get('due_date'):
                task_line += f" (Due: {task['due_date']})"
            if task.get('priority') in [3, 5]:  # Medium or High priority
                task_line += " [Priority]"
            if task.get('tags'):
                task_line += f" [Tags: {', '.join(task['tags'])}]"
            task_list_str += task_line + "\n"

        return task_list_str

    def _generate_task_plan_with_pm(self, goal: str, context: str = "", temperature: float = 0.3) -> List[Dict[str, Any]]:
        """Generate task plan using prompt_manager.

        Uses prompt_manager to generate prompts and parses the LLM response.

        Args:
            goal: The main goal/objective to decompose
            context: Additional context or constraints
            temperature: Creativity level for plan generation.

        Returns:
            List of task dictionaries with title, content, and day_offset.

        Raises:
            RuntimeError: If LLM call fails or returns invalid JSON.
        """
        try:
            # Generate prompts using prompt_manager
            user_prompt = self.pm.render_planner_prompt(goal, context)
            system_prompt = self.pm.get_system_prompt()

            # Call LLM with JSON response format
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content.strip()
            self.logger.debug(f"LLM raw response: {content[:200]}...")

            # Parse JSON response
            import json
            data = json.loads(content)

            # Validate response structure
            if not isinstance(data, dict):
                raise json.JSONDecodeError("Expected JSON object at top level", content, 0)

            tasks = data.get("tasks", [])
            if not isinstance(tasks, list):
                raise json.JSONDecodeError("'tasks' should be a list", content, 0)

            # Validate each task structure
            validated_tasks = []
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    self.logger.warning(f"Task {i} is not a dictionary, skipping")
                    continue

                # Ensure required fields
                if "title" not in task or not task["title"]:
                    self.logger.warning(f"Task {i} missing title, skipping")
                    continue

                # Set defaults for optional fields
                validated_task = {
                    "title": str(task.get("title", "")).strip(),
                    "content": str(task.get("content", "")).strip(),
                    "day_offset": int(task.get("day_offset", 0))
                }
                validated_tasks.append(validated_task)

            return validated_tasks

        except Exception as e:
            self.logger.error(f"Failed to generate task plan with prompt_manager: {e}")
            raise RuntimeError(f"LLM task planning failed: {e}")

    def run_strategic_war_room(self) -> None:
        """Strategic War Room: Continuous conversation loop for daily logging.

        This mode allows users to continuously log their status throughout the day.
        AI provides real-time guidance and all interactions are logged for
        evening review.
        """
        print("\n" + "=" * 50)
        print("🏢 战略指挥室 (Strategic War Room)")
        print("=" * 50)
        print("随时汇报状态，AI将实时指导")
        print("已自动记录所有对话到日志")
        print("")
        print("特殊命令:")
        print("  /done [任务名] - 快速完成任务并记录")
        print("  /review      - 结束今日，生成复盘报告")
        print("  /quit        - 仅记录不复盘，直接退出")
        print("  /exit        - 同上，别名")
        print("-" * 50)

        while True:
            try:
                user_input = input("\n🏔️ > ").strip()

                if not user_input:
                    continue

                # Special command processing
                if user_input.startswith("/done"):
                    self._process_done_command(user_input)
                    continue
                elif user_input in ["/review", "/总结今天"]:
                    self._trigger_daily_review()
                    break
                elif user_input in ["/quit", "/exit"]:
                    print("\n📝 退出战略指挥室（今日记录已保存）")
                    break

                # Regular input processing
                self._process_stream_input(user_input)

            except KeyboardInterrupt:
                print("\n\n⚠️  中断: 退出战略指挥室")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                self.logger.error(f"Strategic war room error: {e}")

    def _process_stream_input(self, user_input: str) -> None:
        """Process user input in stream mode.

        Records user input, generates AI response, and saves to logs.
        """
        # 1. Record user input to log
        self.log_manager.add_log_entry("user_input", user_input)

        # 2. Get recent logs for context
        recent_logs = self.log_manager.format_logs_for_prompt(limit=5)

        # 3. Generate AI response using prompt_manager
        print("\n🤖 AI思考中...")
        try:
            prompt = self.pm.render_stream_response_prompt(user_input, recent_logs)
            ai_response = self.llm.chat(
                prompt,
                system_prompt=self.pm.get_system_prompt(),
                temperature=0.4,
                max_tokens=200
            )

            # 4. Record AI response to log
            self.log_manager.add_log_entry("ai_response", ai_response)

            # 5. Display response (handle special Silent Logging case)
            self._display_stream_response(ai_response)

        except Exception as e:
            error_msg = f"AI响应失败: {e}"
            print(f"❌ {error_msg}")
            self.logger.error(f"LLM response failed: {e}")

    def _display_stream_response(self, ai_response: str) -> None:
        """Display AI response. 
        
        If [Audit Note] is present, display a warning tag BUT also show the AI's actual response.
        """
        print("\n" + "─" * 40)

        # 清洗掉可能存在的 markdown 标记以便处理
        clean_response = ai_response.strip()

        if "[Audit Note]" in clean_response:
            # 1. 显示审计标记 (作为额外动作)
            print("📝 [系统标记] ⚠️ 负面情绪/状态偏差已捕获并归档")
            
            # 2. 移除标记，提取 AI 的实际回复内容
            # 假设标记在开头或结尾，我们将其剔除
            actual_content = clean_response.replace("[Audit Note]", "").replace("记录负面偏差，待总结复盘原因（方法论 vs 输入量）。", "").strip()
            
            # 3. 如果剔除后还有内容，显示出来
            if actual_content:
                print(f"👤 {actual_content}")
        else:
            # 正常响应
            print(f"👤 {clean_response}")

        print("─" * 40)

    def _process_done_command(self, command: str) -> None:
        """Process /done command to mark task completion.

        Args:
            command: The full command string (e.g., "/done Learn Python").
        """
        try:
            # Parse task name
            task_name = command[5:].strip()  # Remove "/done "
            if not task_name:
                print("❌ 请输入任务名称: /done [任务名]")
                return

            print(f"🔍 正在完成任务: {task_name}")

            # Note: Currently we just record the completion in logs
            # In future, could integrate with DidaClient to actually complete tasks
            log_content = f"完成任务: {task_name}"
            self.log_manager.add_log_entry("task_completion", log_content)

            print(f"✅ 已记录完成: {task_name}")

        except Exception as e:
            print(f"❌ 处理完成命令失败: {e}")
            self.logger.error(f"Process done command failed: {e}")

    def _trigger_daily_review(self) -> None:
        """Trigger end-of-day review generation.

        Collects today's logs, tasks, and generates comprehensive report.
        """
        print("\n🔍 正在生成今日复盘报告...")

        # 1. Collect data from logs
        daily_logs = self.log_manager.get_today_logs()
        print(f"📊 今日记录数量: {len(daily_logs)}")

        # 2. Get tasks from TickTick
        try:
            print("📡 读取 TickTick 任务状态...")
            tasks = self.dida.get_inbox_tasks()

            # Extract completed tasks from logs (assume tasks with "task_completion" type)
            completed_from_logs = []
            for log in daily_logs:
                if log.get("type") == "task_completion":
                    content = log.get("content", "")
                    if "完成任务:" in content:
                        task_name = content.replace("完成任务:", "").strip()
                        completed_from_logs.append(task_name)

            pending_tasks = [t['title'] for t in tasks]
            tasks_data = {
                "completed": completed_from_logs,
                "pending": pending_tasks
            }

            print(f"📋 待办任务: {len(pending_tasks)}, 完成记录: {len(completed_from_logs)}")

        except Exception as e:
            print(f"⚠️  无法读取任务数据: {e}")
            self.logger.warning(f"Failed to get tasks for review: {e}")
            tasks_data = {"completed": [], "pending": []}

        # 3. Generate report using enhanced prompt_manager
        print("🧠 生成 AI 复盘报告...")
        try:
            prompt = self.pm.render_auditor_prompt(
                tasks_data=tasks_data,
                daily_logs=daily_logs,
                user_input=""
            )
            report = self.llm.chat(
                prompt,
                system_prompt=self.pm.get_system_prompt(),
                temperature=0.4,
                max_tokens=1500
            )

            # 4. Save report and handle Obsidian integration
            self._save_daily_review(report)

            # Optional: Clear today's logs for fresh start tomorrow
            clear_prompt = input("\n❓ 是否清空今日日志？(y/n): ").lower().strip()
            if clear_prompt == 'y':
                if self.log_manager.clear_today_logs():
                    print("🧹 今日日志已清空")
                else:
                    print("⚠️  日志清空失败")

        except Exception as e:
            print(f"❌ 生成复盘报告失败: {e}")
            self.logger.error(f"Failed to generate daily review: {e}")

    def _save_daily_review(self, report: str) -> None:
        """Save daily review report and integrate with Obsidian if configured.

        Args:
            report: The generated daily review report in Markdown format.
        """
        try:
            # Save to local file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"DailyReview_{timestamp}.md"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# Daily Review - {date_str}\n\n")
                f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                f.write(report)

            print(f"📄 报告已保存: {filename}")

            # Integrate with Obsidian if configured
            obsidian_path = os.getenv("OBSIDIAN_DAILY_PATH")
            if obsidian_path:
                self._append_to_obsidian_daily(report, date_str)

        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            self.logger.error(f"Failed to save daily review: {e}")

    def _append_to_obsidian_daily(self, report: str, date_str: str) -> None:
        """Append the daily review report to Obsidian daily note.

        Args:
            report: The daily review report in Markdown format.
            date_str: Date string for the report.
        """
        try:
            obsidian_path = os.getenv("OBSIDIAN_DAILY_PATH")
            if not obsidian_path:
                return

            print(f"📝 尝试追加到 Obsidian: {obsidian_path}")

            # Check if file exists, create if not
            if not os.path.exists(obsidian_path):
                self.logger.info(f"Obsidian daily file not found, creating: {obsidian_path}")
                with open(obsidian_path, "w", encoding="utf-8") as f:
                    f.write(f"# Daily Note - {date_str}\n\n")

            # Append report to file
            with open(obsidian_path, "a", encoding="utf-8") as f:
                f.write("\n\n---\n")
                f.write("# AI Daily Review\n")
                f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
                f.write(report)

            self.logger.info(f"Report appended to Obsidian: {obsidian_path}")
            print(f"✅ 复盘报告已追加到 Obsidian 日记")

        except Exception as e:
            self.logger.error(f"Failed to append to Obsidian: {e}")
            print(f"⚠️  Obsidian 集成失败: {e}")

    def start(self) -> None:
        """Start the main application loop.

        Presents a menu to the user and handles their choices between
        planning, review, dashboard, strategic war room, and exit options.
        """
        while True:
            print("\n" + "=" * 40)
            print("🎯 AI Personal Project Manager")
            print("=" * 40)
            print("1. 新计划 (New Plan - Goal decomposition)")
            print("2. 每日复盘 (Daily Review - Task report)")
            print("3. AI仪表盘 (Dashboard - Global analysis)")
            print("4. 战略指挥室 (Strategic War Room - Continuous logging) 🆕")
            print("0. 退出 (Exit)")

            choice = input("\nSelect function: ").strip().lower()

            if choice == '1':
                self.run_planner()
            elif choice == '2':
                self.run_auditor()
            elif choice == '3':
                self.run_dashboard()
            elif choice == '4':
                self.run_strategic_war_room()
            elif choice in ['0', 'q']:
                print("\n👋 再见！")
                break
            else:
                print("无效输入，请输入 1, 2, 3, 4 或 0")

    def process_wechat_message(self, user_id: str, content: str) -> str:
        """处理来自微信的消息，返回 AI 的回复。
        
        Args:
            user_id: 微信用户ID (用来区分不同用户的 Context，如果只是自己用可以忽略)
            content: 用户发送的文本
            
        Returns:
            AI 的回复文本
        """
        # 1. 记录用户输入 (利用现有的 LogManager)
        # 可以在 Log 中增加一个 source 字段标记来源是 WeChat
        self.log_manager.add_log_entry("user_input", content)
        
        # 2. 特殊命令拦截 (/done, /review 等)
        if content.startswith("/done"):
            self._process_done_command(content)
            return f"✅ 已记录完成: {content[5:].strip()}"
        elif content in ["/review", "/总结今天"]:
            # 这里需要改造 _trigger_daily_review 让它返回字符串而不是直接打印
            report = self._generate_review_text_only() 
            return report

        # 3. 正常的流式对话逻辑 (复用现有的 Prompt 逻辑)
        recent_logs = self.log_manager.format_logs_for_prompt(limit=5)
        
        try:
            prompt = self.pm.render_stream_response_prompt(content, recent_logs)
            ai_response = self.llm.chat(
                prompt,
                system_prompt=self.pm.get_system_prompt(),
                temperature=0.4,
                max_tokens=300
            )
            
            # 记录 AI 回复
            self.log_manager.add_log_entry("ai_response", ai_response)
            
            # 处理 [Audit Note] 标签，使其适合微信显示
            if "[Audit Note]" in ai_response:
                clean_response = ai_response.replace("[Audit Note]", "").strip()
                return f"⚠️ [系统标记] 负面情绪已归档\n----------------\n{clean_response}"
            
            return ai_response

        except Exception as e:
            self.logger.error(f"WeChat process error: {e}")
            return f"❌ 系统错误: {str(e)}"

    def _generate_review_text_only(self) -> str:
        """辅助方法：生成复盘报告并返回字符串，而不是打印"""
        # ... 把原 _trigger_daily_review 的逻辑复制过来，把 print 改成 return ...
        # 核心是调用 LLM 生成 report，保存文件，然后 return report
        pass

def main() -> None:
    """Main entry point for the AI Project Manager application."""
    try:
        app = AIProjectManager()
        app.start()
    except KeyboardInterrupt:
        print("\n\n[Exit] Application interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
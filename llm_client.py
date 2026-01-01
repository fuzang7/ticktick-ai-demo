import os
import json
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv(override=True)

class LLMClient:
    """
    通用 AI 客户端 (基于 DeepSeek)
    负责与 LLM 进行对话，支持普通聊天和结构化 JSON 输出。
    """
    
    # DeepSeek 配置
    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat" # 指向 DeepSeek-V3
    
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("未找到 DEEPSEEK_API_KEY，请检查 .env 文件")
            
        # 初始化 OpenAI 客户端 (DeepSeek 兼容)
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.DEFAULT_BASE_URL
        )
        logger.info("DeepSeek AI 客户端初始化完成")

    def chat(self, prompt: str, system_prompt: str = "你是我的得力助手") -> str:
        """
        进行一次简单的对话
        """
        try:
            response = self.client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7, # 适中的创造力
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI 调用失败: {e}")
            return f"Error: {str(e)}"

    def get_json_plan(self, goal: str, context: str = "") -> List[Dict[str, Any]]:
        """
        任务拆解器 (升级版：支持时间规划)
        """
        
        system_prompt = """
        你是一名专业的项目经理。你的任务是将用户的目标拆解为具体的子任务，并规划执行时间。
        
        【重要规则】
        1. 返回合法的 JSON 格式。
        2. JSON 必须包含 'tasks' 键，对应一个列表。
        3. 每个任务包含：
           - 'title': 任务标题 (动词开头，如"安装环境")
           - 'content': 执行建议
           - 'day_offset': 执行时间偏移量 (整数)。
             0 表示今天，1 表示明天，2 表示后天，以此类推。
        4. 任务数量 3-7 个。
        5. 必须按执行顺序排列。
        """
        
        user_prompt = f"我的目标是：{goal}\n\n补充背景信息：{context}\n\n请帮我拆解。"

        try:
            response = self.client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={ "type": "json_object" }, # DeepSeek 支持 JSON 模式
                temperature=0.3 # 降低创造力，提高格式稳定性
            )
            
            content = response.choices[0].message.content
            logger.debug(f"AI 原始返回: {content}")
            
            # 解析 JSON
            data = json.loads(content)
            return data.get("tasks", [])
            
        except json.JSONDecodeError:
            logger.error("AI 返回的不是合法的 JSON")
            return []
        except Exception as e:
            logger.error(f"任务拆解失败: {e}")
            return []

if __name__ == "__main__":
    # 简单的自测代码
    client = LLMClient()
    
    print("\n--- 🧪 测试 1: 普通对话 ---")
    reply = client.chat("用一句话介绍一下你自己")
    print(f"AI 回复: {reply}")
    
    print("\n--- 🧪 测试 2: 任务拆解 (JSON) ---")
    goal = "一周内学会 Python 爬虫基础"
    tasks = client.get_json_plan(goal)
    
    print(f"目标: {goal}")
    print(f"AI 拆解出了 {len(tasks)} 个步骤：")
    for i, t in enumerate(tasks):
        print(f"  {i+1}. {t['title']}")
        print(f"     -> {t['content'][:30]}...")
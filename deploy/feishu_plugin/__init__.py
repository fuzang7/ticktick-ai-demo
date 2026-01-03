# 文件位置: chatgpt-on-wechat/plugins/strategic_auditor/__init__.py

import os
import sys
import plugins
from plugins import *
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger

# ============================================================
# ⚠️ 关键修改点：指向你的 ticktick-ai-demo 所在的【绝对路径】
# 比如你的项目在 C:\MyCode\ticktick-ai-demo，就填下面这样
# 注意 Windows 路径要用 r"..." 包裹，或者用双反斜杠 \\
# ============================================================
MY_PROJECT_PATH = r"C:\MyDownload\program\ticktick-ai-demo"

# 把你的项目路径加入 Python 搜索库，这样才能 import main
if MY_PROJECT_PATH not in sys.path:
    sys.path.append(MY_PROJECT_PATH)

# 现在可以从你的项目中导入类了！
try:
    from main import AIProjectManager
except ImportError as e:
    logger.error(f"[StrategicAuditor] 导入失败，请检查路径是否正确: {e}")
    raise e

@plugins.register(
    name="StrategicAuditor",
    desire_priority=999,  # 999 代表最高优先级，你的插件先说话
    hidden=False,
    desc="个人战略执行审计官"
)
class StrategicAuditor(Plugin):
    def __init__(self):
        super().__init__()
        # 监听“处理上下文”事件，也就是收到消息的时候
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        
        # 切换工作目录到你的项目下，确保能读取到 .env 和 logs
        # 这步很重要，否则 log 文件夹会建在 chatgpt-on-wechat 里面
        original_cwd = os.getcwd()
        try:
            os.chdir(MY_PROJECT_PATH)
            print(f"[StrategicAuditor] 正在初始化 AI 大脑...")
            self.manager = AIProjectManager()
            print(f"[StrategicAuditor] 战略指挥室已就绪！")
        except Exception as e:
            logger.error(f"[StrategicAuditor] 初始化失败: {e}")
        finally:
            # 恢复原来的工作目录，以免影响 chatgpt-on-wechat 其他功能
            os.chdir(original_cwd)

    def on_handle_context(self, e_context: EventContext):
        # 1. 过滤掉非文本消息（比如图片、语音）
        if e_context["context"].type != ContextType.TEXT:
            return

        content = e_context["context"].content
        
        # 可以在这里打印一下，看看收到了什么
        logger.info(f"[StrategicAuditor] 收到消息: {content}")

        # 2. 调用你的 AIProjectManager 处理消息
        try:
            # 临时切换目录去处理消息（为了写 log）
            original_cwd = os.getcwd()
            os.chdir(MY_PROJECT_PATH)
            
            # === 调用你在 main.py 里新写的接口 ===
            # user_id 这里传入 session_id，区分不同用户
            reply_text = self.manager.process_wechat_message(
                user_id=e_context["context"]["session_id"], 
                content=content
            )
            
            os.chdir(original_cwd)

            # 3. 构建回复发给微信
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = reply_text
            
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 拦截！不要让默认的 ChatGPT 再回复了

        except Exception as e:
            logger.error(f"[StrategicAuditor] 处理出错: {e}")
            # 如果出错，可以选择不拦截，让它报错或者不回复
            e_context.action = EventAction.CONTINUE
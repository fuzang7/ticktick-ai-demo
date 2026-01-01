import sys
from datetime import datetime
from dida_client import DidaClient
from llm_client import LLMClient
import logging

# 降低日志级别，保持界面清爽
logging.basicConfig(level=logging.ERROR)

class AIProjectManager:
    def __init__(self):
        print("🤖 正在初始化 AI 项目经理...")
        try:
            self.dida = DidaClient()
            self.llm = LLMClient()
            print("✅ 系统就绪！已连接滴答清单 & DeepSeek 大脑")
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            sys.exit(1)

    def run_planner(self):
        """核心功能 1: 目标拆解与规划"""
        print("\n" + "="*40)
        print("🎯 智能规划模式 (The Planner)")
        print("="*40)
        
        goal = input("\n请告诉我你的大目标 (例如: '一周内入门 Linux 驱动开发'):\n> ").strip()
        if not goal: return

        print(f"\n🧠 正在思考如何拆解 '{goal}' ... (请稍候)")
        
        # 1. 调用 AI 拆解
        # 这里你可以把 context 换成更具体的信息，比如你现在的水平
        tasks = self.llm.get_json_plan(goal, context="用户是 C 语言熟练工，偏好实战")
        
        if not tasks:
            print("❌ AI 思考失败，请重试。")
            return

        # 2. 展示方案供用户确认 (Human-in-the-loop)
        print(f"\n📋 AI 建议拆解为 {len(tasks)} 个步骤:")
        for i, t in enumerate(tasks):
            print(f"  [{i+1}] {t['title']}")
            print(f"      └─ {t['content']}")
        
        confirm = input("\n❓ 是否将这些任务写入收集箱？(y/n): ").lower()
        
        # 3. 执行写入
        if confirm == 'y':
            print("\n🚀 正在写入滴答清单...")
            success_count = 0
            for t in tasks:
                # 调用 dida_client 创建任务
                res = self.dida.create_task(title=t['title'], content=t['content'])
                if res:
                    print(f"  ✅ 已创建: {t['title']}")
                    success_count += 1
                else:
                    print(f"  ❌ 创建失败: {t['title']}")
            
            print(f"\n✨ 完成！成功创建 {success_count}/{len(tasks)} 个任务。")
            print("💡 提示：你可以去手机 App 给它们安排具体日期了。")
        else:
            print("👌 已取消操作。")

    def run_auditor(self):
        """核心功能 2: 每日复盘与日报生成"""
        print("\n" + "="*40)
        print("📝 每日复盘模式 (The Auditor)")
        print("="*40)
        
        print("📡 正在读取收集箱任务状态...")
        tasks = self.dida.get_inbox_tasks()
        
        if not tasks:
            print("⚠️ 收集箱是空的，没法复盘。")
            return

        # 简单区分完成/未完成 (注意：API 返回的任务通常包含 status 字段)
        # status: 0=Normal, 2=Completed (具体数值可能随 API 版本变动，这里做简单处理)
        # 注：Open API /data 接口通常只返回未完成的任务，除非特定参数。
        # 这里我们假设拿到的是待办列表，让 AI 基于“待办堆积”做复盘
        
        task_titles = [t['title'] for t in tasks[:10]] # 取前10个避免 token 溢出
        task_str = "\n".join(f"- {t}" for t in task_titles)
        
        print(f"\n🔍 发现你收集箱里还有 {len(tasks)} 个任务待处理。")
        
        user_input = input("\n请简单说一下今天的进展 (例如 '完成了驱动编译，但卡在加载模块上'):\n> ")
        
        prompt = f"""
        用户当前的滴答清单收集箱里堆积了以下任务：
        {task_titles}
        
        用户对自己今日进展的描述：
        "{user_input}"
        
        请你扮演一个极具洞察力的复盘教练，生成一份简短的日报。
        要求：
        1. 格式为 Markdown。
        2. 包含【今日成就】、【遇到的障碍】、【明日建议】三个部分。
        3. 语气要理性、客观，带有鼓励性。
        """
        
        print("\n🧠 正在生成日报...")
        report = self.llm.chat(prompt)
        
        print("\n" + "-"*20 + " 生成结果 " + "-"*20)
        print(report)
        print("-" * 50)
        
        # 可选：保存到本地文件
        save = input("\n❓ 是否保存为 Markdown 文件？(y/n): ").lower()
        if save == 'y':
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"DailyReview_{date_str}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"✅ 已保存到本地: {filename}")

    def start(self):
        while True:
            print("\n🎯 AI 个人项目经理")
            print("1. 新建计划 (拆解任务 -> 滴答清单)")
            print("2. 每日复盘 (读取清单 -> 生成日报)")
            print("q. 退出")
            
            choice = input("\n请选择功能: ").strip().lower()
            
            if choice == '1':
                self.run_planner()
            elif choice == '2':
                self.run_auditor()
            elif choice == 'q':
                print("👋 Bye!")
                break
            else:
                print("无效输入")

if __name__ == "__main__":
    app = AIProjectManager()
    app.start()
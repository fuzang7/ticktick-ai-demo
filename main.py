import sys
from datetime import datetime, timedelta
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
        """核心功能 1: 目标拆解与规划 (父子任务 + 时间版)"""
        print("\n" + "="*40)
        print("🎯 智能规划模式 (Planner V2.0)")
        print("="*40)
        
        goal = input("\n请告诉我你的大目标 (例如: '一周内入门 Linux 驱动开发'):\n> ").strip()
        if not goal: return

        print(f"\n🧠 正在思考如何拆解 '{goal}' ...")
        
        # 1. 调用 AI 拆解 (带时间规划)
        tasks = self.llm.get_json_plan(goal, context="用户希望循序渐进")
        
        if not tasks:
            print("❌ AI 思考失败，请重试。")
            return

        # 2. 展示方案
        print(f"\n📋 AI 建议方案:")
        print(f"   大目标: {goal}")
        now = datetime.now()
        
        for i, t in enumerate(tasks):
            offset = t.get('day_offset', 0)
            # 计算预计日期
            plan_date = now + timedelta(days=offset)
            date_str = plan_date.strftime("%m-%d")
            print(f"   [{i+1}] {date_str} | {t['title']}")

        confirm = input("\n❓ 是否执行写入？(y/n): ").lower()
        
        if confirm == 'y':
            print("\n🚀 正在写入滴答清单...")
            
            # --- 核心修改：先创建父任务 ---
            parent_task = self.dida.create_task(
                title=f"【项目】{goal}", # 加个前缀区分
                content="由 AI 自动规划生成的项目任务组",
                is_all_day=True,
                due_date=now.strftime("%Y-%m-%dT00:00:00+0800") # 父任务设为今天开始
            )
            
            if not parent_task:
                print("❌ 父任务创建失败，流程终止。")
                return
            
            parent_id = parent_task['id']
            print(f"  ✅ 父任务已创建: {goal}")

            # --- 循环创建子任务 ---
            success_count = 0
            for t in tasks:
                # 计算 ISO 8601 格式的日期字符串
                offset = t.get('day_offset', 0)
                due_dt = now + timedelta(days=offset)
                # 格式示例: 2023-10-27T00:00:00+0800
                due_date_str = due_dt.strftime("%Y-%m-%dT00:00:00+0800")
                
                res = self.dida.create_task(
                    title=t['title'], 
                    content=t['content'],
                    parent_id=parent_id,    # <--- 关键：绑定父亲
                    due_date=due_date_str,  # <--- 关键：设置时间
                    is_all_day=True
                )
                
                if res:
                    print(f"    └─ ✅ 子任务: {t['title']} ({due_dt.strftime('%m-%d')})")
                    success_count += 1
                else:
                    print(f"    └─ ❌ 失败: {t['title']}")
            
            print(f"\n✨ 完成！在滴答清单中创建了 1 个父任务和 {success_count} 个子任务。")
        else:
            print("👌 已取消。")

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
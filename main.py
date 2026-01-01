"""AI Project Manager - Integrates TickTick task management with LLM planning.

This application combines TickTick API for task management with LLM capabilities
for intelligent task planning and daily review generation.
"""

import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dida_client import DidaClient
from llm_client import LLMClient


class AIProjectManager:
    """Main application that integrates TickTick task management with AI planning.

    This manager provides two core functionalities:
    1. Goal decomposition and task planning with time scheduling
    2. Daily review and progress report generation

    Attributes:
        dida (DidaClient): TickTick API client
        llm (LLMClient): LLM client for AI planning and analysis
    """

    def __init__(self):
        """Initialize the AI Project Manager.

        Raises:
            SystemExit: If initialization fails due to configuration or connection issues.
        """
        # Configure logging for this module only
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        print("🤖 Initializing AI Project Manager...")
        try:
            self.dida = DidaClient()
            self.llm = LLMClient()
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
            tasks = self.llm.generate_task_plan(
                goal,
                context="User wants a gradual, step-by-step approach",
                num_tasks=5,  # Default to 5 tasks for reasonable decomposition
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
        """Core function 2: Daily review and progress report generation.

        This method:
        1. Retrieves current tasks from TickTick inbox
        2. Asks user for daily progress report
        3. Uses LLM to generate a structured daily review
        4. Optionally saves the review as a Markdown file
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

        # Build prompt for LLM
        prompt = f"""
        The user currently has the following tasks pending in their TickTick inbox:
        {task_titles}

        The user's description of today's progress:
        "{user_input}"

        Please act as an insightful review coach and generate a brief daily report.
        Requirements:
        1. Format in Markdown.
        2. Include these sections: [Today's Achievements], [Challenges Encountered], [Suggestions for Tomorrow].
        3. Tone should be rational, objective, and encouraging.
        4. Keep it concise (3-5 paragraphs total).
        """

        print("\n🧠 Generating daily report...")
        try:
            report = self.llm.chat(
                prompt,
                system_prompt="You are an insightful productivity coach who helps "
                            "users reflect on their daily progress and plan for tomorrow.",
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

        # Optionally save to file
        save = input("\n❓ Save as Markdown file? (y/n): ").lower().strip()
        if save == 'y':
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"DailyReview_{date_str}.md"
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(report)
                print(f"✅ Saved to local file: {filename}")
            except Exception as e:
                print(f"❌ Failed to save file: {e}")

    def start(self) -> None:
        """Start the main application loop.

        Presents a menu to the user and handles their choices between
        planning, review, and exit options.
        """
        while True:
            print("\n" + "=" * 40)
            print("🎯 AI Personal Project Manager")
            print("=" * 40)
            print("1. New Plan (Decompose goals -> TickTick)")
            print("2. Daily Review (Read tasks -> Generate report)")
            print("q. Quit")

            choice = input("\nSelect function: ").strip().lower()

            if choice == '1':
                self.run_planner()
            elif choice == '2':
                self.run_auditor()
            elif choice == 'q':
                print("\n👋 Goodbye!")
                break
            else:
                print("Invalid input. Please enter 1, 2, or q.")


def main() -> None:
    """Main entry point for the AI Project Manager application."""
    try:
        app = AIProjectManager()
        app.start()
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
"""TickTick (Dida365) API Client for AI applications.

This module provides a client for interacting with the TickTick (Dida365) API,
specifically designed for AI-powered task management applications.
"""

import os
import logging
from typing import Optional, Dict, List, Any
import requests
from dotenv import load_dotenv
from ticktick.oauth2 import OAuth2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

class DidaClient:
    """TickTick (Dida365) API client for AI task management.

    This client provides methods to interact with the TickTick API including
    task creation, retrieval, and management with OAuth2 authentication.

    Attributes:
        base_url (str): TickTick API base URL
        client_id (str): OAuth2 client ID from TickTick developer portal
        client_secret (str): OAuth2 client secret from TickTick developer portal
        redirect_uri (str): OAuth2 redirect URI registered in TickTick developer portal
        inbox_id (str): TickTick inbox project ID (optional)
        session (requests.Session): HTTP session with authentication headers
    """

    # Default configuration
    DEFAULT_BASE_URL = "https://api.dida365.com/open/v1"
    DEFAULT_TOKEN_FILE = ".token-oauth"
    DEFAULT_USER_AGENT = "TickTickAI/1.0 (Python)"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        inbox_id: Optional[str] = None,
        base_url: Optional[str] = None,
        token_file: Optional[str] = None
    ):
        """Initialize the DidaClient.

        Args:
            client_id: OAuth2 client ID. If not provided, reads from TICKTICK_CLIENT_ID env var.
            client_secret: OAuth2 client secret. If not provided, reads from TICKTICK_CLIENT_SECRET env var.
            redirect_uri: OAuth2 redirect URI. If not provided, reads from TICKTICK_REDIRECT_URI env var.
            inbox_id: Inbox project ID. If not provided, reads from TICKTICK_INBOX_ID env var.
            base_url: API base URL. Defaults to https://api.dida365.com/open/v1.
            token_file: Path to token file. Defaults to .token-oauth.
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.token_file = token_file or self.DEFAULT_TOKEN_FILE

        # Get credentials from environment if not provided
        self.client_id = client_id or os.getenv("TICKTICK_CLIENT_ID", "").strip()
        self.client_secret = client_secret or os.getenv("TICKTICK_CLIENT_SECRET", "").strip()
        self.redirect_uri = redirect_uri or os.getenv("TICKTICK_REDIRECT_URI", "").strip()
        self.inbox_id = inbox_id or os.getenv("TICKTICK_INBOX_ID", "").strip()

        # Validate required configuration
        if not self.client_id or not self.client_secret:
            logger.warning("Client ID and/or Client Secret not configured")

        self.session = requests.Session()
        self._load_token()

    def _load_token(self) -> None:
        """Load and refresh OAuth2 token.

        Raises:
            FileNotFoundError: If token file doesn't exist.
            ValueError: If token cannot be loaded.
        """
        if not os.path.exists(self.token_file):
            error_msg = f"Token file not found: {self.token_file}. Please run authentication script first."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            # Use ticktick library to handle token refresh
            oauth = OAuth2(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri
            )

            # Get access token
            raw_token = oauth.get_access_token()
            token = raw_token.get("access_token") if isinstance(raw_token, dict) else str(raw_token)

            if not token:
                raise ValueError("Failed to extract access token")

            # Update session headers
            self.session.headers.update({
                "Authorization": f"Bearer {token}",
                "User-Agent": self.DEFAULT_USER_AGENT,
                "Content-Type": "application/json"
            })

            logger.info("Token loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load token: {e}")
            raise ValueError(f"Token loading failed: {e}")

    def get_inbox_tasks(self) -> List[Dict[str, Any]]:
        """Retrieve all tasks from the inbox.

        Returns:
            List of task dictionaries. Each task contains title, id, content, etc.

        Examples:
            >>> client = DidaClient()
            >>> tasks = client.get_inbox_tasks()
            >>> for task in tasks[:5]:
            ...     print(f"Task: {task['title']}")
        """
        if not self.inbox_id:
            logger.warning("TICKTICK_INBOX_ID not configured, inbox operations disabled")
            return []

        url = f"{self.base_url}/project/{self.inbox_id}/data"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('tasks', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve inbox tasks: {e}")
            if hasattr(e.response, 'text'):
                logger.debug(f"Response: {e.response.text}")
            return []
        except ValueError as e:
            logger.error(f"Failed to parse response JSON: {e}")
            return []
    def create_task(
        self,
        title: str,
        content: str = "",
        project_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        due_date: Optional[str] = None,
        time_zone: Optional[str] = None,
        is_all_day: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Create a new task in TickTick.

        Args:
            title: Task title (required)
            content: Task description or content (optional)
            project_id: Project ID to create task in. If None, uses inbox_id.
            parent_id: Parent task ID for creating subtasks (optional)
            due_date: Due date in ISO 8601 format (e.g., "2023-10-01T00:00:00+08:00")
            time_zone: Time zone for the due date (e.g., "Asia/Shanghai").
                      If None and due_date provided, defaults to "Asia/Shanghai".
            is_all_day: Whether the task is all-day (default True).

        Returns:
            Dictionary containing created task data if successful, None otherwise.

        Raises:
            ValueError: If title is empty or required configuration missing.
            ValueError: If due_date is provided but not in valid ISO 8601 format.

        Examples:
            >>> client = DidaClient()
            >>> task = client.create_task("Review documentation", "Check API updates")
            >>> print(f"Created task ID: {task['id']}")
        """
        if not title.strip():
            raise ValueError("Task title cannot be empty")

        # Validate due date format if provided
        if due_date:
            # Basic ISO 8601 format validation
            import re
            iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'
            if not re.match(iso_pattern, due_date):
                raise ValueError(
                    f"Invalid due_date format: {due_date}. "
                    "Expected ISO 8601 format: YYYY-MM-DDTHH:MM:SS±HH:MM"
                )

        target_project_id = project_id or self.inbox_id
        if not target_project_id:
            logger.warning("No project ID specified and inbox_id not configured")
            return None

        url = f"{self.base_url}/task"

        # Base payload
        payload = {
            "title": title.strip(),
            "content": content.strip(),
            "projectId": target_project_id,
            "isAllDay": is_all_day
        }

        # Add parent_id for subtasks
        if parent_id:
            payload["parentId"] = parent_id

        # Add due date and timezone if provided
        if due_date:
            payload["dueDate"] = due_date
            # Use provided timezone or default
            payload["timeZone"] = time_zone or "Asia/Shanghai"

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()

            task_data = response.json()
            logger.info(f"Task created successfully: {title} (ID: {task_data.get('id')})")
            return task_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create task '{title}': {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"API Response: {e.response.text}")
            return None

    def get_project_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve all tasks from a specific project.

        Args:
            project_id: The ID of the project to retrieve tasks from.

        Returns:
            List of task dictionaries from the specified project.
        """
        url = f"{self.base_url}/project/{project_id}/data"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('tasks', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve tasks from project {project_id}: {e}")
            return []

    def update_task(self, task_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update an existing task.

        Args:
            task_id: ID of the task to update
            **kwargs: Task fields to update (title, content, etc.)

        Returns:
            Updated task data if successful, None otherwise.
        """
        url = f"{self.base_url}/task/{task_id}"
        try:
            response = self.session.put(url, json=kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return None

    def delete_task(self, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_id: ID of the task to delete

        Returns:
            True if deletion successful, False otherwise.
        """
        url = f"{self.base_url}/task/{task_id}"
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            logger.info(f"Task {task_id} deleted successfully")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Retrieve all projects from TickTick.

        Returns:
            List of project dictionaries. Each project contains id, name, type, etc.

        Raises:
            requests.exceptions.RequestException: If API request fails.
        """
        url = f"{self.base_url}/project"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            projects = response.json()

            # Filter out system projects if needed
            # Inbox typically has type "INBOX", other user projects have type "TASK"
            logger.info(f"Retrieved {len(projects)} projects")
            return projects

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve projects: {e}")
            if hasattr(e.response, 'text'):
                logger.debug(f"Response: {e.response.text}")
            raise  # Re-raise to let caller handle

    def get_project_tasks_batch(
        self,
        project_ids: List[str],
        delay_between_requests: float = 0.5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve tasks from multiple projects with rate limiting.

        Args:
            project_ids: List of project IDs to fetch tasks from
            delay_between_requests: Delay in seconds between API requests to avoid rate limiting

        Returns:
            Dictionary mapping project_id to list of tasks in that project.

        Note:
            This method includes a delay between requests to respect API rate limits.
        """
        import time
        from typing import Dict, List, Any

        results: Dict[str, List[Dict[str, Any]]] = {}

        for i, project_id in enumerate(project_ids):
            try:
                logger.debug(f"Fetching tasks for project {project_id} ({i+1}/{len(project_ids)})")
                tasks = self.get_project_tasks(project_id)
                results[project_id] = tasks

                # Add delay between requests except for the last one
                if i < len(project_ids) - 1:
                    time.sleep(delay_between_requests)

            except Exception as e:
                logger.error(f"Failed to fetch tasks for project {project_id}: {e}")
                results[project_id] = []  # Empty list for failed projects

        logger.info(f"Fetched tasks from {len(results)} projects, total tasks: {sum(len(tasks) for tasks in results.values())}")
        return results

    def get_active_tasks_from_all_projects(self) -> Dict[str, Any]:
        """Retrieve all active tasks across all projects.

        Returns:
            Dictionary containing:
                - 'projects': List of all projects with metadata
                - 'project_tasks': Dict mapping project_id to list of tasks
                - 'all_tasks': Flattened list of all tasks across all projects
                - 'project_map': Dict mapping project_id to project_name for easy lookup
                - 'summary': Basic statistics about the tasks

        Note:
            This method performs multiple API calls and includes delays to avoid rate limiting.
            It only returns tasks with status indicating they are not completed.
        """
        try:
            # Step 1: Get all projects
            logger.info("Fetching all projects...")
            projects = self.get_all_projects()

            if not projects:
                logger.warning("No projects found")
                return {
                    'projects': [],
                    'project_tasks': {},
                    'all_tasks': [],
                    'project_map': {},
                    'summary': {'total_projects': 0, 'total_tasks': 0}
                }

            # Create project mapping (id -> name) for human-readable output
            project_map = {p['id']: p.get('name', f"Project_{p['id'][:8]}") for p in projects}

            # Step 2: Get tasks from all projects (with rate limiting)
            logger.info(f"Fetching tasks from {len(projects)} projects...")
            project_tasks = self.get_project_tasks_batch(
                project_ids=list(project_map.keys()),
                delay_between_requests=0.5  # 500ms between requests
            )

            # Step 3: Flatten all tasks and add project metadata
            all_tasks = []
            for project_id, tasks in project_tasks.items():
                for task in tasks:
                    # Add project name to each task for easier reference
                    task_with_context = task.copy()
                    task_with_context['project_name'] = project_map.get(project_id, 'Unknown')
                    task_with_context['project_id'] = project_id
                    all_tasks.append(task_with_context)

            # Step 4: Filter for active tasks (not completed)
            # TickTick task status: 0=Normal, 1=Archived, 2=Completed (varies by API version)
            active_tasks = [
                task for task in all_tasks
                if task.get('status', 0) in [0, 1]  # Normal or Archived (not Completed)
            ]

            # Step 5: Create summary
            summary = {
                'total_projects': len(projects),
                'total_tasks': len(all_tasks),
                'active_tasks': len(active_tasks),
                'completed_tasks': len(all_tasks) - len(active_tasks),
                'projects_with_tasks': sum(1 for tasks in project_tasks.values() if tasks)
            }

            logger.info(
                f"Dashboard data collected: {summary['active_tasks']} active tasks "
                f"across {summary['projects_with_tasks']} projects"
            )

            return {
                'projects': projects,
                'project_tasks': project_tasks,
                'all_tasks': all_tasks,
                'active_tasks': active_tasks,
                'project_map': project_map,
                'summary': summary
            }

        except Exception as e:
            logger.error(f"Failed to collect dashboard data: {e}")
            raise RuntimeError(f"Dashboard data collection failed: {e}")

    def prepare_dashboard_data_for_llm(
        self,
        max_tasks: int = 50,
        include_content: bool = True
    ) -> Dict[str, Any]:
        """Prepare task data for LLM analysis with token optimization.

        Args:
            max_tasks: Maximum number of tasks to include in the analysis.
                       If there are more tasks, they will be summarized.
            include_content: Whether to include task content/description.
                           If False, only title, project, and metadata are included.

        Returns:
            Dictionary containing:
                - 'summary': Basic statistics
                - 'tasks': Simplified task data for LLM analysis
                - 'projects': Project information
                - 'analysis_ready': Whether data is ready for LLM analysis
        """
        try:
            # Step 1: Collect all data
            dashboard_data = self.get_active_tasks_from_all_projects()
            active_tasks = dashboard_data['active_tasks']
            project_map = dashboard_data['project_map']
            summary = dashboard_data['summary']

            if not active_tasks:
                logger.warning("No active tasks found for analysis")
                return {
                    'summary': summary,
                    'tasks': [],
                    'projects': list(project_map.values()),
                    'analysis_ready': False,
                    'message': 'No active tasks to analyze'
                }

            # Step 2: Simplify task data for LLM consumption
            simplified_tasks = []
            for task in active_tasks[:max_tasks]:  # Limit to max_tasks
                simplified_task = {
                    'title': task.get('title', 'Untitled'),
                    'project': project_map.get(task.get('project_id', ''), 'Unknown'),
                    'priority': task.get('priority', 'Normal'),  # 0=None, 1=Low, 3=Medium, 5=High
                    'due_date': task.get('dueDate'),
                    'tags': task.get('tags', []),
                    'status': task.get('status', 0),
                }

                # Only include content if requested and task count is manageable
                if include_content and len(active_tasks) <= max_tasks:
                    simplified_task['content'] = task.get('content', '')[:200]  # Limit content length

                # Add additional useful fields if they exist
                if 'startDate' in task:
                    simplified_task['start_date'] = task['startDate']
                if 'repeatFlag' in task:
                    simplified_task['recurring'] = task['repeatFlag']

                simplified_tasks.append(simplified_task)

            # Step 3: Create analysis-ready data structure
            analysis_data = {
                'summary': {
                    'total_active_tasks': summary['active_tasks'],
                    'total_projects': summary['total_projects'],
                    'projects_with_tasks': summary['projects_with_tasks'],
                    'analysis_task_count': len(simplified_tasks),
                    'has_more_tasks': len(active_tasks) > max_tasks
                },
                'tasks': simplified_tasks,
                'projects': [
                    {'id': pid, 'name': name}
                    for pid, name in project_map.items()
                ],
                'analysis_ready': True
            }

            # Step 4: Add categorization hints
            # Categorize tasks by priority
            priority_counts = {'None': 0, 'Low': 0, 'Medium': 0, 'High': 0}
            for task in simplified_tasks:
                priority = task.get('priority', 'None')
                if priority == 0:
                    priority_counts['None'] += 1
                elif priority == 1:
                    priority_counts['Low'] += 1
                elif priority == 3:
                    priority_counts['Medium'] += 1
                elif priority == 5:
                    priority_counts['High'] += 1
                else:
                    priority_counts['None'] += 1

            # Categorize by project
            project_counts = {}
            for task in simplified_tasks:
                project = task.get('project', 'Unknown')
                project_counts[project] = project_counts.get(project, 0) + 1

            analysis_data['categorization'] = {
                'by_priority': priority_counts,
                'by_project': project_counts,
                'projects_with_most_tasks': sorted(
                    project_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]  # Top 5 projects by task count
            }

            # Step 5: Calculate overdue tasks
            from datetime import datetime
            today = datetime.now().date()
            overdue_count = 0
            near_deadline_count = 0

            for task in simplified_tasks:
                due_date_str = task.get('due_date')
                if due_date_str:
                    try:
                        # Parse ISO 8601 date string
                        due_date = datetime.fromisoformat(
                            due_date_str.replace('Z', '+00:00')
                        ).date()
                        days_until_due = (due_date - today).days

                        if days_until_due < 0:
                            overdue_count += 1
                        elif days_until_due <= 3:  # Due in next 3 days
                            near_deadline_count += 1
                    except (ValueError, AttributeError):
                        continue  # Skip if date parsing fails

            analysis_data['summary']['overdue_tasks'] = overdue_count
            analysis_data['summary']['near_deadline_tasks'] = near_deadline_count

            logger.info(
                f"LLM analysis data prepared: {len(simplified_tasks)} tasks, "
                f"{overdue_count} overdue, {priority_counts['High']} high priority"
            )

            return analysis_data

        except Exception as e:
            logger.error(f"Failed to prepare LLM analysis data: {e}")
            raise RuntimeError(f"LLM data preparation failed: {e}")

def main() -> None:
    """Example usage of the DidaClient."""
    try:
        # Initialize client with environment variables
        client = DidaClient()

        # Example: Get inbox tasks
        print("Retrieving inbox tasks...")
        inbox_tasks = client.get_inbox_tasks()
        print(f"Found {len(inbox_tasks)} tasks in inbox")
        if inbox_tasks:
            print("First 3 tasks:")
            for i, task in enumerate(inbox_tasks[:3], 1):
                print(f"  {i}. {task.get('title', 'No title')}")

        # Example: Create a new task
        # Uncomment to create a test task
        # new_task = client.create_task(
        #     "Test task from script",
        #     "This is a test task created by the example script"
        # )
        # if new_task:
        #     print(f"Created task with ID: {new_task.get('id')}")

    except FileNotFoundError as e:
        print(f"Configuration error: {e}")
        print("\nSetup instructions:")
        print("1. Create a .env file with your TickTick API credentials")
        print("2. Run the authentication script to get an access token")
        print("3. Configure TICKTICK_INBOX_ID in .env for inbox operations")
    except ValueError as e:
        print(f"Authentication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
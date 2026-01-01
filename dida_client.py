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
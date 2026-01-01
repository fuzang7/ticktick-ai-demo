# TickTick (Dida365) AI Demo

A Python client library for interacting with the TickTick (Dida365) API, designed for AI-powered task management applications.

## Features

- **AI-Powered Planning**: Decompose goals into actionable tasks using LLMs
- **Smart Task Scheduling**: Automatic time planning with parent-child relationships
- **Daily Review Generation**: AI-assisted progress reports and insights
- **OAuth2 Authentication**: Full OAuth2 flow implementation for secure API access
- **Task Management**: Create, read, update, and delete tasks
- **Inbox Operations**: Specialized methods for inbox task management
- **Project Support**: Retrieve tasks from specific projects
- **Error Handling**: Comprehensive error handling and logging
- **Configuration**: Environment-based configuration with validation

## Installation

### Prerequisites

- Python 3.7 or higher
- TickTick developer account (register at [TickTick Developer Portal](https://developer.dida365.com/openapi))

### Install from requirements.txt

```bash
pip install -r requirements.txt
```

### Dependencies

- `requests`: HTTP client library
- `python-dotenv`: Environment variable management
- `ticktick-py`: TickTick API wrapper (used for token refresh)
- `openai`: OpenAI SDK (compatible with DeepSeek and other LLM providers)
- `certifi`: SSL certificates

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ticktick-ai-demo.git
cd ticktick-ai-demo
```

### 2. Set up environment variables

Create a `.env` file in the project root:

```env
# Required: OAuth2 credentials from TickTick developer portal
TICKTICK_CLIENT_ID=your_client_id_here
TICKTICK_CLIENT_SECRET=your_client_secret_here
TICKTICK_REDIRECT_URI=http://localhost:8080/callback

# Optional: Inbox ID for inbox-specific operations
TICKTICK_INBOX_ID=your_inbox_id_here

# Required for AI features: DeepSeek API key
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 3. Authenticate with TickTick

Run the authentication script:

```bash
python refresh_token.py
```

Follow the instructions in the terminal to complete the OAuth2 flow.

### 4. Run the main application

```bash
python main.py
```

This will start the AI Project Manager with the following menu:
```
🎯 AI Personal Project Manager
========================================
1. New Plan (Decompose goals -> TickTick)
2. Daily Review (Read tasks -> Generate report)
q. Quit
```

### 5. Basic client usage examples

```python
from dida_client import DidaClient
from llm_client import LLMClient

# Initialize clients
dida = DidaClient()
llm = LLMClient()

# Example 1: Get inbox tasks
tasks = dida.get_inbox_tasks()
print(f"You have {len(tasks)} tasks in your inbox")

# Example 2: Use AI for task planning
goal = "Learn Python web scraping in one week"
ai_tasks = llm.generate_task_plan(goal, num_tasks=5)
for i, task in enumerate(ai_tasks, 1):
    print(f"Day {task['day_offset']}: {task['title']}")

# Example 3: Create tasks in TickTick
parent_task = dida.create_task(
    title=f"[Project] {goal}",
    content="AI-generated project plan",
    due_date="2024-12-31T00:00:00+08:00"
)
if parent_task:
    print(f"Created parent task: {parent_task['id']}")
```

## API Reference

### DidaClient Class

#### Initialization

```python
client = DidaClient(
    client_id="your_client_id",      # Optional, defaults to TICKTICK_CLIENT_ID env var
    client_secret="your_secret",     # Optional, defaults to TICKTICK_CLIENT_SECRET env var
    redirect_uri="http://localhost", # Optional, defaults to TICKTICK_REDIRECT_URI env var
    inbox_id="inbox_123",            # Optional, defaults to TICKTICK_INBOX_ID env var
    base_url="https://api.dida365.com/open/v1",  # Optional API base URL
    token_file=".token-oauth"        # Optional token file path
)
```

#### Methods

- `get_inbox_tasks()`: Retrieve all tasks from the inbox
- `create_task(title, content="", project_id=None)`: Create a new task
- `get_project_tasks(project_id)`: Retrieve tasks from a specific project
- `update_task(task_id, **kwargs)`: Update an existing task
- `delete_task(task_id)`: Delete a task

### Authentication Script

The `refresh_token.py` script handles the complete OAuth2 authorization flow:

1. Validates configuration
2. Generates authorization URL
3. Guides user through browser authorization
4. Exchanges authorization code for access token
5. Saves token to file

## Configuration Details

### Obtaining TickTick API Credentials

1. Visit [TickTick Developer Portal](https://developer.dida365.com/openapi)
2. Create a new application
3. Note your Client ID and Client Secret
4. Register a Redirect URI (e.g., `http://localhost:8080/callback`)

### Finding Your Inbox ID

The inbox ID is a unique identifier for your TickTick inbox. To find it:

1. Use the TickTick API to list all projects
2. Look for the project with type `INBOX`
3. Alternatively, inspect API responses when working with tasks

## Examples

### Basic Usage

```python
from dida_client import DidaClient

client = DidaClient()

# List recent tasks
tasks = client.get_inbox_tasks()
print(f"You have {len(tasks)} tasks in your inbox")

# Create tasks from a list
todo_items = [
    "Finish project proposal",
    "Schedule team meeting",
    "Review pull requests"
]

for item in todo_items:
    client.create_task(item)
    print(f"Added: {item}")
```

### Error Handling

```python
from dida_client import DidaClient

try:
    client = DidaClient()

    # Attempt to create a task without title
    task = client.create_task("")  # This will raise ValueError

except ValueError as e:
    print(f"Validation error: {e}")

except FileNotFoundError as e:
    print(f"Configuration error: {e}")
    print("Please run the authentication script first")

except Exception as e:
    print(f"Unexpected error: {e}")
```

### Batch Operations

```python
from dida_client import DidaClient

client = DidaClient()

# Update multiple tasks
tasks = client.get_inbox_tasks()
for task in tasks:
    if "urgent" in task['title'].lower():
        client.update_task(task['id'], tags=["urgent", "priority"])
        print(f"Marked as urgent: {task['title']}")

# Delete completed tasks
for task in tasks:
    if task.get('status') == 2:  # Status 2 indicates completed
        if client.delete_task(task['id']):
            print(f"Deleted completed task: {task['title']}")
```

## Security Considerations

- **Token Storage**: Access tokens are stored in `.token-oauth` file. Keep this file secure.
- **Environment Variables**: Never commit `.env` files to version control.
- **Permissions**: The OAuth2 scope is limited to `tasks:read` and `tasks:write`.
- **Token Expiration**: Tokens expire and need to be refreshed. The client handles this automatically.

## Troubleshooting

### Common Issues

1. **"Token file not found"**: Run `python refresh_token.py` to authenticate
2. **"Invalid credentials"**: Verify your Client ID and Secret in `.env`
3. **"Authorization code invalid"**: Authorization codes are single-use; get a new one
4. **"Redirect URI mismatch"**: Ensure the redirect URI matches exactly in TickTick portal

### Logging

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [TickTick](https://ticktick.com/) for their excellent task management API
- The `ticktick-py` library for OAuth2 token refresh implementation
- All contributors and users of this project

## Support

For questions, issues, or feature requests, please:

1. Check the [existing issues](https://github.com/yourusername/ticktick-ai-demo/issues)
2. Open a new issue if your problem isn't already addressed
3. Include detailed information about your setup and the error
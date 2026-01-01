"""LLM Client for AI-powered task management.

This module provides a client for interacting with Large Language Models (LLMs),
specifically designed for task planning and analysis in conjunction with TickTick.
Currently supports DeepSeek API compatible with OpenAI SDK.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)


class LLMClient:
    """Client for Large Language Model interactions.

    This client provides methods to interact with LLMs for task planning,
    analysis, and general conversation. Currently configured for DeepSeek API.

    Attributes:
        client (OpenAI): OpenAI-compatible client instance
        model (str): LLM model name to use
        base_url (str): API base URL
    """

    # Default configuration for DeepSeek
    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize the LLMClient.

        Args:
            api_key: API key for LLM service. If not provided, reads from DEEPSEEK_API_KEY env var.
            base_url: API base URL. Defaults to https://api.deepseek.com.
            model: LLM model name. Defaults to "deepseek-chat".

        Raises:
            ValueError: If API key is not provided or found in environment.
        """
        # Get configuration from parameters or environment
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL

        if not self.api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY not found. Please add it to your .env file or "
                "provide it as a parameter."
            )

        # Initialize OpenAI-compatible client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        logger.info(f"LLM client initialized with model: {self.model}")

    def chat(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Perform a simple chat conversation with the LLM.

        Args:
            prompt: User prompt/message
            system_prompt: System prompt defining the assistant's role
            temperature: Creativity level (0.0-2.0). Higher is more creative.
            max_tokens: Maximum tokens to generate. If None, uses model default.

        Returns:
            Assistant's response as string.

        Examples:
            >>> client = LLMClient()
            >>> response = client.chat("What is Python?")
            >>> print(response)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise RuntimeError(f"Failed to get response from LLM: {e}")

    def generate_task_plan(
        self,
        goal: str,
        context: str = "",
        num_tasks: Optional[int] = None,
        temperature: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Generate a task plan by decomposing a goal into subtasks.

        This method uses the LLM to break down a goal into actionable subtasks
        with time planning information.

        Args:
            goal: The main goal/objective to decompose
            context: Additional context or constraints
            num_tasks: Number of subtasks to generate (3-7). If None, let the LLM decide.
            temperature: Creativity level for plan generation. Lower values produce
                        more consistent/structured outputs.

        Returns:
            List of task dictionaries, each containing:
                - title: Task title (action-oriented)
                - content: Detailed description or instructions
                - day_offset: Days from today to schedule this task (0=today, 1=tomorrow, etc.)

        Raises:
            RuntimeError: If LLM call fails or returns invalid JSON
            json.JSONDecodeError: If LLM response is not valid JSON

        Examples:
            >>> client = LLMClient()
            >>> tasks = client.generate_task_plan("Learn Python basics in one week")
            >>> for task in tasks:
            ...     print(f"Day {task['day_offset']}: {task['title']}")
        """
        # Build system prompt
        system_prompt = """You are a professional project manager. Your task is to decompose
        user goals into specific subtasks with time planning.

        RULES:
        1. Return valid JSON format.
        2. JSON must contain a 'tasks' key with a list of tasks.
        3. Each task must have:
           - 'title': Task title (start with a verb, e.g., "Install environment")
           - 'content': Execution suggestions or detailed instructions
           - 'day_offset': Integer representing days from today (0=today, 1=tomorrow, etc.)
        4. Generate 3-7 tasks depending on goal complexity.
        5. Tasks must be in execution order.
        6. Make tasks actionable and specific."""

        if num_tasks:
            system_prompt += f"\n7. Generate exactly {num_tasks} tasks."

        # Build user prompt
        user_prompt = f"My goal is: {goal}"
        if context:
            user_prompt += f"\n\nAdditional context: {context}"
        user_prompt += "\n\nPlease help me break this down into actionable tasks."

        try:
            # Note: response_format parameter structure depends on the API
            # OpenAI format: response_format={"type": "json_object"}
            # Some implementations may require different structure
            create_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "stream": False
            }

            # Try different response_format formats
            try:
                # Try OpenAI standard format
                create_params["response_format"] = {"type": "json_object"}
                response = self.client.chat.completions.create(**create_params)
            except Exception as format_error:
                logger.debug(f"Standard response_format failed, trying alternative: {format_error}")
                # Try alternative format or omit if not supported
                try:
                    del create_params["response_format"]
                    response = self.client.chat.completions.create(**create_params)
                except Exception as inner_error:
                    logger.error(f"LLM call failed: {inner_error}")
                    raise RuntimeError(f"Failed to get response from LLM: {inner_error}")

            content = response.choices[0].message.content.strip()
            logger.debug(f"LLM raw response: {content[:200]}...")

            # Parse JSON response
            data = json.loads(content)

            # Validate response structure
            if not isinstance(data, dict):
                raise json.JSONDecodeError(
                    "Expected JSON object at top level",
                    content, 0
                )

            tasks = data.get("tasks", [])
            if not isinstance(tasks, list):
                raise json.JSONDecodeError(
                    "'tasks' should be a list",
                    content, 0
                )

            # Validate each task structure
            validated_tasks = []
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    logger.warning(f"Task {i} is not a dictionary, skipping")
                    continue

                # Ensure required fields
                if "title" not in task or not task["title"]:
                    logger.warning(f"Task {i} missing title, skipping")
                    continue

                # Set defaults for optional fields
                validated_task = {
                    "title": str(task.get("title", "")).strip(),
                    "content": str(task.get("content", "")).strip(),
                    "day_offset": int(task.get("day_offset", 0))
                }
                validated_tasks.append(validated_task)

            if not validated_tasks:
                logger.warning("No valid tasks generated")
                return []

            logger.info(f"Generated {len(validated_tasks)} tasks for goal: {goal[:50]}...")
            return validated_tasks

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from LLM: {e}")
            raise
        except Exception as e:
            logger.error(f"Task planning failed: {e}")
            raise RuntimeError(f"Failed to generate task plan: {e}")

def main() -> None:
    """Example usage of the LLMClient."""
    try:
        client = LLMClient()

        print("=" * 60)
        print("LLM Client Example Usage")
        print("=" * 60)

        # Test 1: Simple chat
        print("\n[Test 1: Simple Chat]")
        try:
            response = client.chat(
                "Introduce yourself in one sentence",
                system_prompt="You are a helpful AI assistant"
            )
            print(f"Assistant: {response}")
        except Exception as e:
            print(f"Chat test failed: {e}")

        # Test 2: Task planning
        print("\n[Test 2: Task Planning]")
        try:
            goal = "Learn web scraping basics in one week"
            tasks = client.generate_task_plan(goal, num_tasks=4)

            print(f"Goal: {goal}")
            print(f"Generated {len(tasks)} tasks:")
            for i, task in enumerate(tasks, 1):
                print(f"  {i}. Day {task['day_offset']}: {task['title']}")
                if task['content']:
                    print(f"     Details: {task['content'][:60]}...")
        except Exception as e:
            print(f"Task planning test failed: {e}")

        print("\n" + "=" * 60)
        print("Example usage completed")

    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease add DEEPSEEK_API_KEY to your .env file:")
        print("DEEPSEEK_API_KEY=your_api_key_here")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
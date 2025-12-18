from strands import Agent, tool, ToolContext
from strands.models.openai import OpenAIModel
from strands_tools import calculator
from strands.session.file_session_manager import FileSessionManager

import os
from dotenv import load_dotenv
load_dotenv()

import logging
# Enable debug logging to see the agent's thought process
logging.basicConfig(level=logging.INFO)
logging.getLogger("strands").setLevel(logging.INFO)

# LLM config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
model = OpenAIModel(
    client_args={"api_key": OPENAI_API_KEY},
    model_id="gpt-5-nano",
)

## create a file session manger to persist agent state across runs
session_manager = FileSessionManager(storage_dir=".", session_id="session_123")

@tool(context=True)
def track_user_action(action: str, tool_context: ToolContext):
    """Track user actions in agent state.

    Args:
        action: The action to track
    """
    # Get current action count
    action_count = tool_context.agent.state.get("action_count") or 0

    # Update state
    tool_context.agent.state.set("action_count", action_count + 1)
    tool_context.agent.state.set("last_action", action)

    return f"Action '{action}' recorded. Total actions: {action_count + 1}"

@tool(context=True)
def get_user_stats(tool_context: ToolContext):
    """Get user statistics from agent state."""
    action_count = tool_context.agent.state.get("action_count") or 0
    last_action = tool_context.agent.state.get("last_action") or "none"

    return f"Actions performed: {action_count}, Last action: {last_action}"

# initialized the agent with tools
agent = Agent(
    model=model,
    tools=[track_user_action, get_user_stats, calculator],
    session_manager=session_manager,
    system_prompt="You are a helpful assistant"
)

agent("Track that I logged in")
agent("Track that I viewed my profile")
print(f"Actions taken: {agent.state.get('action_count')}")
print(f"Last action: {agent.state.get('last_action')}")

# Get conversation messages
print(agent.messages)

# Get entire state
all_state = agent.state.get()
print(all_state)  # All state data as a dictionary
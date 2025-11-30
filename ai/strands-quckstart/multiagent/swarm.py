import logging
from strands import Agent
from strands.multiagent import Swarm
from strands.models.openai import OpenAIModel
import os
from dotenv import load_dotenv
load_dotenv()

# Enable debug logs and print them to stderr
logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

## model config 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

model = OpenAIModel(
  client_args={"api_key": OPENAI_API_KEY},
  # **model_config
  model_id= "gpt-5-nano",
  # params={
    # "max_completion_tokens": 1000,
    # "temperature": 0.2,
  # }
)
# Create specialized agents
researcher = Agent(model= model,name="researcher", system_prompt="You are a research specialist...")
coder = Agent(model= model, name="coder", system_prompt="You are a coding specialist...")
reviewer = Agent(model = model, name="reviewer", system_prompt="You are a code review specialist...")
architect = Agent(model = model, name="architect", system_prompt="You are a system architecture specialist...")

# Create a swarm with these agents, starting with the researcher
swarm = Swarm(
    [coder, researcher, reviewer, architect],
    entry_point=researcher,  # Start with the researcher
    max_handoffs=20,
    max_iterations=20,
    execution_timeout=900.0,  # 15 minutes
    node_timeout=300.0,       # 5 minutes per agent
    repetitive_handoff_detection_window=8,  # There must be >= 3 unique agents in the last 8 handoffs
    repetitive_handoff_min_unique_agents=3
)

# Execute the swarm on a task
result = swarm("Design and implement a simple REST API for a todo app")

# Access the final result
print(f"Status: {result.status}")
print(f"Node history: {[node.node_id for node in result.node_history]}")
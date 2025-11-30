import logging
import os
from dotenv import load_dotenv
load_dotenv()
from strands import Agent, tool
from strands.multiagent import Swarm
from strands.models.openai import OpenAIModel


## Agent config 
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

# Enable debug logs and print them to stderr
logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)


initial_agent = Agent(name="initial_agent",
  system_prompt=(
    "You are a cyber security analyst.(SOC L1 Analyst). Try to summerize and trige the alert given by the user and provide inital investigation(triage) question."),
  model=model )
query_agent = Agent(name="query_agent",
  system_prompt=(
    "You are a cyber security analyst.(SOC L1 Analyst). You will query the Elastic SIEM tools with Elasticsearch Query Language (ES|QL) to get more information about the alert. Given the alert information from the initial agent, generate ES|QL queries to gather more context about the alert. Provide only the ES|QL queries without any additional explanation."),
  model=model )
l1_agent = Agent(name="l1_agent",
  system_prompt=(
    "You are a cyber security analyst.(SOC L1 Analyst). You will provide the final analysis report based on the information gathered from the initial agent and query agent."),
  model=model )



swarm = Swarm(
  [initial_agent, query_agent, l1_agent],
    entry_point=initial_agent,
    max_handoffs=10,
    max_iterations=10,
    execution_timeout=600.0,  # 10 minutes
    node_timeout=180.0,       # 3 minutes per agent
    repetitive_handoff_detection_window=5,
    repetitive_handoff_min_unique_agents=2
)

# Ask the agent for an analysis of a security alert
message = """{
  "rule.name": "M365 Identity – Login from Impossible Travel Location",
  "@timestamp": "2025-01-15T03:41:22.112Z",
  "event.category": "authentication",
  "event.action": "signin_success",
  "user.name": "saw.naung",
  "user.id": "AABBCC1122",
  "source.geo.country_name": "United States",
  "source.geo.city_name": "Chicago",
  "source.ip": "23.18.55.91",
  "related.previous_login": {
      "timestamp": "2025-01-15T03:15:05.909Z",
      "source.geo.country_name": "Canada",
      "source.geo.city_name": "Toronto",
      "source.ip": "152.199.21.45"
  },
  "impossible_travel": {
    "distance_km": 702,
    "time_diff_minutes": 26,
    "required_speed_kmh": 1617,
    "threshold_kmh": 900,
    "is_impossible": true
  },
  "threat.indicator": "Unusual location jump — potential account takeover"
}"""

result = swarm(message)

# final_result = result.results['l1_agent'].result
# print(f"Final Analysis Report:\n{final_result}")

# Check execution status
print(f"Status: {result.status}")  # COMPLETED, FAILED, etc.

# See which agents were involved
for node in result.node_history:
    print(f"Agent: {node.node_id}")

# Get the output from the query agent (guard against it not running)
if 'query_agent' in result.results:
  query_result = result.results['query_agent'].result
  print(f"Query Agent Output:\n{query_result}")
else:
  print("query_agent did not run — available agent results:")
  for agent_name, node in result.results.items():
    # node may be an object with .result or a plain value — handle both
    node_result = getattr(node, 'result', node)
    print(f" - {agent_name}: {node_result}")
import logging
import os
from dotenv import load_dotenv
load_dotenv()
from strands import Agent, tool
from strands.multiagent import Swarm
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from strands.session.file_session_manager import FileSessionManager


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

## create a file session manger to persist agent state across runs
session_manager = FileSessionManager(storage_dir=".", session_id="l1_agent_session")

## elastic-mcp client config
MCP_URL = os.getenv("ELASTIC_MCP_URL", "http://172.16.10.105:5601/api/agent_builder/mcp")
MCP_APIKEY = os.getenv("ELASTIC_MCP_APIKEY")

elastic_mcp_client = MCPClient(
    lambda: streamablehttp_client(
        url=MCP_URL,
        headers={"Authorization": f"ApiKey {MCP_APIKEY}"},
    )
)
elastic_mcp_client.start()
elastic_tool = elastic_mcp_client.list_tools_sync()
# # Returns a list of available tools adapted to the AgentTool interface
# print("Elastic MCP Tools:")
# for tool in elastic_tool:
#   print(f"- {tool.tool_name}")


initial_agent = Agent(name="initial_agent",
  system_prompt=(
    "You are a cyber security analyst.(SOC L1 Analyst). Try to summarize and triage the alert given by the user and provide initial investigation (triage) questions. "
    "If you determine more specialized follow-up is needed, CALL the swarm coordination tool `handoff_to_agent` to pass control to the correct agent. "
    "Example (exact usage understood by the orchestration tool): handoff_to_agent('l1_agent', 'Please continue triage, collect artifacts and gather virtualization details', {'reason': 'escalation for artifact collection'})"
  ),
  model=model )
l1_agent = Agent(
  name="l1_agent",
  tools=elastic_tool,
  system_prompt=(
    "You are a cyber security analyst.(SOC L1 Analyst). You will provide the final analysis report based on the information gathered from the initial agent and query agent."),
  model=model )



swarm = Swarm(
  [initial_agent, l1_agent],
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
Title : "Virtual Machine Fingerprinting"
Source event:	AZrXM-M3jgoeGott3xeD
host.name:	ca-server
agent.status:	Healthy
user.name:	ubuntu
process.executable:	/usr/bin/cat
kibana.alert.rule.type:	query
process.name:	cat
process.parent.name:	bash
process.args:	cat/proc/scsi/scsi
}"""

result = swarm(message)

# final_result = result.results['l1_agent'].result
# print(f"Final Analysis Report:\n{final_result}")

# Check execution status
print(f"Status: {result.status}")  # COMPLETED, FAILED, etc.

# See which agents were involved
for node in result.node_history:
    print(f"Agent: {node.node_id}")


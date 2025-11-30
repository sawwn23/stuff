from strands import Agent
from strands.models.openai import OpenAIModel
from dotenv import load_dotenv
load_dotenv()
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import os
import logging

logging.getLogger("strands").setLevel(logging.DEBUG)

# Sets the logging format and streams logs to stderr
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

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
# Returns a list of available tools adapted to the AgentTool interface
print("Elastic MCP Tools:")
for tool in elastic_tool:
  print(f"- {tool.tool_name}")

agent = Agent(
    model=model,
    tools=elastic_tool,
    system_prompt=(
        "You are a cyber security analyst. You will use the Elastic MCP tools to conduct threat hunting on given hunt mission and provide analysis reports."
    )
)


hunt_mission = """Hunt for any suspicious login activities to Linux servers from unusual locations in the last 7 days. Provide a summary of findings including any indicators of compromise (IOCs) and recommended remediation steps."""

agent(hunt_mission)
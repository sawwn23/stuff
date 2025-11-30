from strands import Agent
from strands.models.openai import OpenAIModel
import os
from dotenv import load_dotenv
load_dotenv()
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

agent = Agent(model=model)

agent("Tell me about MCP in AI.")
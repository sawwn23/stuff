from strands import Agent, tool
from strands.models.openai import OpenAIModel
import os
from dotenv import load_dotenv
load_dotenv()
from strands_tools import calculator
from tools import get_order_status, lookup_return_policy, initiate_refund
import logging

# Enable debug logging to see the agent's thought process
logging.basicConfig(level=logging.INFO)
logging.getLogger("strands").setLevel(logging.DEBUG)

## LLM config 
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


# Define the agent's persona and instructions
SYSTEM_PROMPT = """
You are a helpful and efficient customer support assistant for an online retailer.
Your goal is to resolve customer issues accurately and quickly.
You have access to the following tools:
- get_order_status: To check the status of a customer's order.
- lookup_return_policy: To provide information about return policies for different product categories.
- initiate_refund: To start the refund process for an order.
- calculator: To perform any necessary calculations.

Follow these rules:
1. Be polite and empathetic in all your responses.
2. Before using a tool that requires an order ID, always confirm the order ID with the customer if it was not provided.
3. Do not make up information. If you cannot answer a question with your available tools, say so.
"""

# Instantiate the agent
support_agent = Agent(
    model=model,
    tools=[
        get_order_status,
        lookup_return_policy,
        initiate_refund,
        calculator
    ],
    system_prompt=SYSTEM_PROMPT
)

def main():
    print("Customer Support Agent is ready. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Invoke the agent
        response = support_agent(user_input)
        print(f"Agent: {response.message}")

if __name__ == "__main__":
    main()

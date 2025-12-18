## What is Agent Loop

Agent loop follows these steps:

Receives user input and contextual information
Processes the input using a language model (LLM)
Decides whether to use tools to gather information or perform actions
Executes tools and receives results
Continues reasoning with the new information
Produces a final response or iterates again through the loop

## Example AgentLoop logs

Add this sample output (copied from a run of `python ./agent_loop.py`) to show expected debug/telemetry output from the agent:

```
python ./agent_loop.py
DEBUG:strands.models.openai:config=<{ 'model_id': 'gpt-5-nano' }> | initializing
DEBUG:strands.tools.loader:tool_name=<calculator>, module=<calculator> | loading tools from module
DEBUG:strands.tools.loader:tool_name=<calculator>, module=<calculator> | found function-based tool in module
DEBUG:strands.tools.registry:tool_name=<calculator>, tool_type=<function>, is_dynamic=<False> | registering tool
DEBUG:strands.tools.registry:tools_dir=</Users/sawwinnaung/Documents/02_Personal/stuff/ai/strands-quckstart/concepts/tools> | tools directory not found
DEBUG:strands.tools.registry:tool_modules=<[]> | discovered
DEBUG:strands.tools.registry:tool_count=<0>, success_count=<0> | finished loading tools
DEBUG:strands.tools.registry:getting tool configurations
DEBUG:strands.tools.registry:tool_name=<calculator> | loaded tool config
DEBUG:strands.tools.registry:tool_count=<1> | tools configured
DEBUG:strands.tools.registry:getting tool configurations
DEBUG:strands.tools.registry:tool_name=<calculator> | loaded tool config
DEBUG:strands.tools.registry:tool_count=<1> | tools configured
INFO:strands.telemetry.metrics:Creating Strands MetricsClient
DEBUG:strands.tools.registry:getting tool configurations
DEBUG:strands.tools.registry:tool_name=<calculator> | loaded tool config
DEBUG:strands.tools.registry:tool_count=<1> | tools configured
DEBUG:strands.event_loop.streaming:model=<<strands.models.openai.OpenAIModel object at 0x105bb37c0>> | streaming messages
DEBUG:strands.models.openai:formatting request
DEBUG:strands.models.openai:formatted request=<
{
	"messages": [
		{
			"role": "system",
			"content": "You are a helpful assistant"
		},
		{
			"role": "user",
			"content": [
				{ "text": "What is 25 multiplied by 4?", "type": "text" }
			]
		}
	],
	"model": "gpt-5-nano",
	"stream": true,
	"stream_options": { "include_usage": true },
	"tools": [
		{
			"type": "function",
			"function": {
				"name": "calculator",
				"description": "Calculator powered by SymPy for comprehensive mathematical operations. (trimmed here for readability)",
				"parameters": {
					"type": "object",
					"required": ["expression"],
					"properties": {
						"expression": { "type": "string", "description": "Expression to evaluate (e.g. \"2 + 2 * 3\")" },
						"mode": { "type": "string", "description": "evaluate|solve|derive|integrate|limit|series|matrix" },
						"precision": { "type": "integer" },
						"scientific": { "type": "boolean" },
						"force_numeric": { "type": "boolean" },
						"variables": { "type": "object" },
						"wrt": { "type": "string" },
						"point": { "type": "string" },
						"order": { "type": "integer" }
					}
				}
			}
		}
	]
}
>
DEBUG:strands.models.openai:invoking model
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
DEBUG:strands.models.openai:got response from model
DEBUG:strands.models.openai:finished streaming response from model
DEBUG:strands.agent.conversation_manager.sliding_window_conversation_manager:message_count=<2>, window_size=<40> | skipping context reduction
25 multiplied by 4 equals 100.%
```

## State

Strands Agents state is maintained in several forms:

Conversation History: The sequence of messages between the user and the agent.
Agent State: Stateful information outside of conversation context, maintained across multiple requests.
Request State: Contextual information maintained within a single request.

### Conversation History

Default is the **sliding_window_conversation_manager**

```
DEBUG:strands.agent.conversation_manager.sliding_window_conversation_manager:message_count=<2>, window_size=<40> | skipping context reduction
```

The sliding window conversation manager:

Keeps the most recent N message pairs
Removes the oldest messages when the window size is exceeded
Handles context window overflow exceptions by reducing context
Ensures conversations don't exceed model context limits

```
{'role': 'user', 'content': [{'text': 'What is 25 multiplied by 4?'}]}, {'role': 'assistant', 'content': [{'text': '100'}]}]
```

### Agent State

Basically it's a kv store unlike conversation history, agent state is not passed to the model during inference but can be accessed and modified by tools and application logic.

```
INFO:strands.telemetry.metrics:Creating Strands MetricsClient
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"

Tool #1: track_user_action
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
Done. I’ve logged that you logged in. Total actions tracked so far: 1.

INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
Would you like me to show your full activity stats or log another action?
Tool #2: track_user_action
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
Done. I’ve logged that you viewed your profile. Total actions tracked so far: 2.

Would you like me to show your full activity stats or log another action?Actions taken: 2
Last action: user_viewed_profile
[{'role': 'user', 'content': [{'text': 'Track that I logged in'}]}, {'role': 'assistant', 'content': [{'toolUse': {'toolUseId': 'call_pNYv0bGQJuTWxSK6GbZETasJ', 'name': 'track_user_action', 'input': {'action': 'user_logged_in'}}}]}, {'role': 'user', 'content': [{'toolResult': {'toolUseId': 'call_pNYv0bGQJuTWxSK6GbZETasJ', 'status': 'success', 'content': [{'text': "Action 'user_logged_in' recorded. Total actions: 1"}]}}]}, {'role': 'assistant', 'content': [{'text': 'Done. I’ve logged that you logged in. Total actions tracked so far: 1.\n\nWould you like me to show your full activity stats or log another action?'}]}, {'role': 'user', 'content': [{'text': 'Track that I viewed my profile'}]}, {'role': 'assistant', 'content': [{'toolUse': {'toolUseId': 'call_qUbwwV3dZ69CN9V9KcmwNFTc', 'name': 'track_user_action', 'input': {'action': 'user_viewed_profile'}}}]}, {'role': 'user', 'content': [{'toolResult': {'toolUseId': 'call_qUbwwV3dZ69CN9V9KcmwNFTc', 'status': 'success', 'content': [{'text': "Action 'user_viewed_profile' recorded. Total actions: 2"}]}}]}, {'role': 'assistant', 'content': [{'text': 'Done. I’ve logged that you viewed your profile. Total actions tracked so far: 2.\n\nWould you like me to show your full activity stats or log another action?'}]}]
{'action_count': 2, 'last_action': 'user_viewed_profile'}
```

### Session Management

Single Agent Sessions: - Conversation history (messages) - Agent state (key-value storage) - Other stateful information (like Conversation Manager)

Multi-Agent Sessions: - Orchestrator state and configuration - Individual agent states and result within the orchestrator - Cross-agent shared state and context - Execution flow and node transition history

Strands provides built-in session persistence capabilities that automatically capture and restore this information, allowing agents and multi-agent systems to seamlessly continue conversations where they left off.

1.FileSessionManager: Stores sessions in the local filesystem
2.S3SessionManager: Stores sessions in Amazon S3 buckets

```
{
  "agent_id": "default",
  "state": {
    "action_count": 2,
    "last_action": "viewed_profile"
  },
  "conversation_manager_state": {
    "__name__": "SlidingWindowConversationManager",
    "removed_message_count": 0
  },
  "_internal_state": {
    "interrupt_state": {
      "interrupts": {},
      "context": {},
      "activated": false
    }
  },
  "created_at": "2025-11-30T20:51:25.280348+00:00",
  "updated_at": "2025-11-30T20:51:38.237473+00:00"
}
```

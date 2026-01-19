# Elastic Security MCP Server

A Model Context Protocol (MCP) server that translates natural language queries into Elasticsearch Query Language (ES|QL) for SOC analysts and threat hunters.

## Architecture

**Single-file FastMCP server** following MCP best practices:

```
ai/elastic-security-mcp/
├── server.py          # Complete MCP server (tools, resources, prompts)
├── test_mcp.py        # Core functionality tests
├── requirements.txt   # Dependencies
└── README.md         # This file
```

## Core Components

### 🛠️ MCP Tools (7 total)

1. **`get_schema(index_pattern)`** - Get ECS field definitions
2. **`nl_to_esql_plan(params)`** - Parse natural language to structured intent
3. **`generate_esql_query(intent_json)`** - Convert intent to ES|QL
4. **`validate_esql_query(params)`** - Security policy validation
5. **`translate_nl_to_esql(params)`** - Complete NL → ES|QL pipeline

### 📋 Resources

- **`security://schemas`** - Available log schemas and ECS fields
- **`security://templates`** - Hunting templates and patterns
- **`security://policies`** - Security policies and limits

### 💡 Prompts

- **`threat_hunting_guide(category)`** - Category-specific hunting guidance
- **`esql_best_practices()`** - ES|QL query optimization tips

## Supported Use Cases

### Authentication Analysis

```
"Show failed SSH logins from China in the last 6 hours"
```

→ `FROM logs-auth-* | WHERE @timestamp >= NOW() - 6h AND event.category == "authentication" AND event.outcome == "failure" AND source.geo.country_name == "China" AND network.protocol == "ssh" | LIMIT 100`

### Process Hunting

```
"Processes spawned by powershell in the last 2 hours"
```

→ `FROM logs-endpoint-* | WHERE @timestamp >= NOW() - 2h AND event.category == "process" AND process.parent.name == "powershell" | LIMIT 100`

### User Aggregation

```
"Failed authentication attempts by user in the last 12 hours"
```

→ `FROM logs-auth-* | WHERE @timestamp >= NOW() - 12h AND event.category == "authentication" AND event.outcome == "failure" | STATS count() BY user.name | LIMIT 100`

## Natural Language Parser

The NL parser uses **deterministic rule-based patterns** (not LLM-based) for reliability:

### Time Patterns

- "last 6 hours" → `@timestamp >= NOW() - 6h`
- "past 2 days" → `@timestamp >= NOW() - 48h`
- "today" → `@timestamp >= NOW() - 24h`

### Category Detection

- "auth", "login", "logon" → `event.category == "authentication"`
- "process", "spawn", "exec" → `event.category == "process"`
- "network", "connection" → `event.category == "network"`

### Outcome Patterns

- "success", "successful" → `event.outcome == "success"`
- "failed", "failure" → `event.outcome == "failure"`

### Geographic Filters

- "from China" → `source.geo.country_name == "China"`
- "from Russia" → `source.geo.country_name == "Russia"`

### Protocol Detection

- "SSH" → `network.protocol == "ssh"`
- "RDP" → `network.protocol == "rdp"`

## Security Policies

Built-in validation prevents dangerous queries:

- **Time Limits**: Maximum 7 days (168 hours)
- **Result Limits**: Maximum 1000 results
- **Allowed Indexes**: `logs-auth-*`, `logs-endpoint-*`, `logs-network-*`
- **Forbidden Operations**: `JOIN`, `ENRICH`
- **Required Fields**: Time range mandatory for unbounded queries

## ECS Schema Support

### Authentication Logs (`logs-auth-*`)

- `@timestamp`, `event.category`, `event.outcome`
- `user.name`, `user.domain`
- `source.ip`, `source.geo.country_name`
- `network.protocol`, `network.transport`

### Process Logs (`logs-endpoint-*`)

- `@timestamp`, `event.category`, `process.name`
- `process.parent.name`, `process.command_line`
- `process.pid`, `process.parent.pid`
- `user.name`, `host.name`, `file.path`

### Network Logs (`logs-network-*`)

- `@timestamp`, `source.ip`, `destination.ip`
- `source.port`, `destination.port`
- `network.protocol`, `network.bytes`
- `source.geo.country_name`

## Installation & Usage

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Test Core Functionality

```bash
python test_mcp.py
```

### Run MCP Server

```bash
python server.py
```

### Example MCP Client Usage

```python
# Using the MCP tools
result = await client.call_tool("translate_nl_to_esql", {
    "query": "Show failed SSH logins from China in the last 6 hours"
})

print(result["query"])
# FROM logs-auth-* | WHERE @timestamp >= NOW() - 6h AND ...
```

## Error Handling

### Ambiguous Queries (Rejected)

```
"Show risky logins"
→ Error: "Ambiguous term 'risky' - please specify criteria"
```

### Policy Violations (Blocked)

```
"Show all authentication logs"
→ Error: "Time range required for safety"
```

### Invalid Fields

```
Query using non-ECS fields
→ Error: "Field 'custom.field' not allowed for index 'logs-auth-*'"
```

## Hunting Templates

Pre-built patterns for common threat hunting scenarios:

### Authentication Failures

- Brute force detection
- Geographic anomalies
- Protocol-specific analysis

### Process Spawning

- Suspicious parent-child relationships
- PowerShell abuse detection
- Living off the land techniques

### Network Analysis

- External connections by country
- High volume transfers
- Unusual port activity

## Integration

### Claude Desktop

Add to `mcp.json`:

```json
{
  "mcpServers": {
    "elastic-security": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "ES_HOST": "http://localhost:9200",
        "ES_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Environment Variables

- `ES_HOST`: Elasticsearch endpoint (default: `http://localhost:9200`)
- `ES_API_KEY`: Elasticsearch API key (optional for development)

## Development

The server uses **FastMCP** for clean, FastAPI-style development:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("elastic-security-mcp")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"

@mcp.resource("my://resource")
def my_resource() -> str:
    """Resource description"""
    return json.dumps({"data": "value"})

@mcp.prompt()
def my_prompt(context: str = "default") -> str:
    """Prompt description"""
    return f"Analyze this: {context}"
```

## Production Deployment

For production use:

1. **Connect to real Elasticsearch** (update `ES_HOST`, `ES_API_KEY`)
2. **Extend schema validation** with your actual ECS mappings
3. **Add authentication** and rate limiting
4. **Monitor query performance** and adjust limits
5. **Add logging** for audit trails

## Contributing

The codebase is designed for easy extension:

- **Add new categories**: Extend `category_patterns` in `NLParser`
- **New hunting templates**: Add to `HUNTING_TEMPLATES` dict
- **Custom validation**: Extend `ValidationPolicy` class
- **Additional resources**: Add `@mcp.resource()` decorated functions

## FastMCP Server — Learning Guide

This concise guide summarizes the core concepts and quick examples for building, configuring, and running a FastMCP server. It is based on the FastMCP server documentation and is intended as a practical reference for getting started.

### 1) Quickstart — Create a Server

```python
from fastmcp import FastMCP

mcp = FastMCP(name="MyAssistantServer")

@mcp.tool
def multiply(a: float, b: float) -> float:
    return a * b

if __name__ == "__main__":
    mcp.run()  # runs with STDIO by default
```

Optional constructor arguments include `instructions`, `version`, `website_url`, `icons`, `auth`, `lifespan`, `tools`, and tag filters (`include_tags` / `exclude_tags`).

### 2) Components

- Tools: callable functions exposed to clients via `@mcp.tool`.
- Resources: data endpoints via `@mcp.resource("uri")` and resource templates with URI parameters.
- Prompts: reusable message templates via `@mcp.prompt`.

Example resource template:

```python
@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: int) -> dict:
    return {"id": user_id, "name": f"User {user_id}"}
```

### 3) Tag-Based Filtering

Use `include_tags` and `exclude_tags` to expose only a subset of components: useful for public vs internal views.

Example:

```python
mcp = FastMCP(include_tags={"public"}, exclude_tags={"internal"})
```

### 4) Running and Transport Options

- STDIO: default for local CLI clients.
- HTTP: recommended for web services (Streamable HTTP protocol).
- SSE: legacy transport (deprecated).

Run with HTTP transport:

```python
mcp.run(transport="http", host="0.0.0.0", port=9000)
```

### 5) Custom Routes (HTTP only)

Add simple web endpoints alongside the MCP endpoint using `@mcp.custom_route`.

```python
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return PlainTextResponse("OK")
```

### 6) Composing, Proxying, and Integration

- Compose servers with `mount()` to embed subservers.
- Use `FastMCP.as_proxy()` to proxy remote MCP servers.
- Import OpenAPI or FastAPI apps with `FastMCP.from_openapi()` and `FastMCP.from_fastapi()`.

### 7) Server Configuration & Global Settings

- Server-specific settings passed to constructor (e.g., `on_duplicate_tools`, `include_fastmcp_meta`).
- Global settings via environment variables `FASTMCP_*` (e.g., `FASTMCP_LOG_LEVEL`, `FASTMCP_STRICT_INPUT_VALIDATION`).

### 8) Input Validation Modes

- Default (flexible): Pydantic coercion for LLM-friendly inputs.
- Strict mode: JSON Schema validation to reject mismatched types (`strict_input_validation=True`).

### 9) Custom Tool Serialization

Provide `tool_serializer` to format tool return values (e.g., YAML) for clients.

### 10) Practical Recommendations

- Keep `instructions` concise and include examples for expected tool usage.
- Tag components to create public/internal views.
- Use HTTP transport for production; STDIO for local development and testing.
- Prefer `include_fastmcp_meta=True` during development for richer metadata; consider disabling for simpler client integrations.

---

Reference: FastMCP Server docs — https://gofastmcp.com/servers/server

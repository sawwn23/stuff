from fastmcp import FastMCP

mcp = FastMCP("My MCP Quickstart")

@mcp.tool()
def greet(name: str) -> str:
    """Greet a person by name.
    args:
        name: The name of the person to greet.
    """
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run() # stdio by default
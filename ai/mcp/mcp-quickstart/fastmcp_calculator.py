from fastmcp import FastMCP

mcp = FastMCP(name = "fastmcp_calculator")

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers.
    args:
        a: The first number.
        b: The second number.
    """
    return a * b

@mcp.tool(
    name = "add",
    description = "Add two numbers together.",
    tags = ["arithmetic", "math"]
)
def add_numbers(x: float, y: float) -> float:
    """Add two numbers.
    args:
        x: The first number.
        y: The second number.
    """
    return x + y

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract two numbers.
    args:
        a: The first number.
        b: The second number.
    """
    return a - b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers.
    args:
        a: The numerator.
        b: The denominator.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

if __name__ == "__main__":
    mcp.run() # stdio by default
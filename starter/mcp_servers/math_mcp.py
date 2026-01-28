from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")


@mcp.tool(tags=set(["hallo", "welt"]))
def add(a: int, b: int) -> int:
    """
    Add two numbers.

    Args:
        a: First operand.
        b: Second operand.

    Returns:
        The sum of a and b."""
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """
    Multiply two numbers

    Args 



    """
    return a * b


if __name__ == "__main__":
    mcp.run(transport="http")

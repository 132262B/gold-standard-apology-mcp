"""FastMCP Server Template for AWS Lambda.

This is a boilerplate for creating MCP servers using FastMCP 2.0
with AWS Lambda deployment via Lambda Web Adapter.
"""

import os
from typing import Annotated

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

# Create FastMCP server (stateless for AWS Lambda)
mcp = FastMCP(
    name="my-mcp-server",
    instructions="Your MCP server description here.",
    stateless_http=True,
)


# Example Tool 1: Simple greeting
@mcp.tool()
async def greet(
    name: Annotated[str, "Name to greet"],
) -> dict:
    """Greet a user by name."""
    return {"message": f"Hello, {name}!"}


# Example Tool 2: Calculator
@mcp.tool()
async def calculate(
    operation: Annotated[str, "Operation: add, subtract, multiply, divide"],
    a: Annotated[float, "First number"],
    b: Annotated[float, "Second number"],
) -> dict:
    """Perform basic arithmetic operations."""
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else None,
    }

    if operation not in operations:
        return {"error": f"Unknown operation: {operation}"}

    result = operations[operation](a, b)
    if result is None:
        return {"error": "Division by zero"}

    return {"result": result, "operation": f"{a} {operation} {b}"}


# Example Tool 3: Echo with options
@mcp.tool()
async def echo(
    message: Annotated[str, "Message to echo"],
    uppercase: Annotated[bool, "Convert to uppercase"] = False,
    repeat: Annotated[int, "Number of times to repeat"] = 1,
) -> dict:
    """Echo a message with optional transformations."""
    result = message
    if uppercase:
        result = result.upper()

    return {"echo": " ".join([result] * repeat)}


# Example Tool 4: Environment info
@mcp.tool()
async def get_env_info() -> dict:
    """Get environment information (for debugging)."""
    return {
        "python_version": os.popen("python --version").read().strip(),
        "env_vars_count": len(os.environ),
        "is_lambda": "AWS_LAMBDA_FUNCTION_NAME" in os.environ,
    }


def create_app():
    """Create ASGI app with health check endpoint."""
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

    async def health(request):
        return JSONResponse({"status": "ok"})

    # Get FastMCP's ASGI app
    mcp_app = mcp.http_app(path="/mcp")

    # Create main app with health check and MCP
    app = Starlette(
        routes=[
            Route("/health", health),
            Mount("/", app=mcp_app),
        ],
        lifespan=mcp_app.lifespan,
    )
    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8080)

import random
from typing import Annotated

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP(
    name="kwon-decision",
    instructions="""이 MCP 서버는 선택 장애를 해결해줍니다. 여러 선택지 중 하나를 골라드립니다.""",
    stateless_http=True,
)


@mcp.tool()
async def decide(
    choices: Annotated[list[str], "선택지 목록 (예: ['짬뽕', '짜장면', '울면', '기스면'])"],
) -> str:
    """여러 선택지 중 하나를 랜덤으로 선택해줍니다.

    사용자가 무엇을 선택해야 할지 고민될 때 호출됩니다.
    예: 오늘 뭐 먹지? 짬뽕, 짜장면, 울면, 기스면
    """
    if not choices:
        return "선택지가 없습니다. 선택지를 제공해주세요."

    selected = random.choice(choices)
    return f'권결정의 선택은 "{selected}"'


def create_app():
    """Create ASGI app with health check endpoint."""
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

    async def health(request):
        return JSONResponse({"status": "ok"})

    mcp_app = mcp.http_app(path="/mcp")

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

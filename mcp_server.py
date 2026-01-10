import base64
from typing import Annotated

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP(
    name="horseplay-societ-mcp",
    instructions="""이 MCP 서버는 선택 장애를 해결해줍니다. 여러 선택지 중 하나를 골라드립니다.""",
    stateless_http=True,
)


@mcp.tool()
async def pick(
    choices: Annotated[list[str], "선택지 목록 (예: ['짬뽕', '짜장면', '울면', '기스면'])"],
) -> str:
    """무언가를 선택해야 하거나, 누군가를 뽑아야 할 때 호출됩니다.

    여러 선택지 중 하나를 골라주는 게임 URL을 생성합니다.
    예: 오늘 뭐 먹지? 짬뽕, 짜장면 / 누가 발표할까? 철수, 영희, 민수
    """
    if not choices:
        return "선택지가 없습니다. 선택지를 제공해주세요."

    joined = "||".join(choices)
    encoded = base64.b64encode(joined.encode("utf-8")).decode("utf-8")
    url = f"https://game.baejji.com?query={encoded}"
    return url


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

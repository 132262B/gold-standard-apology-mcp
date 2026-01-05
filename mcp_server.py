from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

PROMPT_TEMPLATE = (Path(__file__).parent / "prompt.md").read_text(encoding="utf-8")

mcp = FastMCP(
    name="gold-standard-apology",
    instructions="""이 MCP 서버는 사과문 작성을 도와줍니다.""",
    stateless_http=True,
)

@mcp.tool()
async def get_apology_system_prompt(
    situation: Annotated[str, "사과해야 하는 상황에 대한 설명 (무슨 일이 있었는지)"],
    relationship: Annotated[str, "사과 대상과의 관계 (예: 연인, 친구, 부모님, 직장 상사, 고객 등)"],
    severity: Annotated[str, "상황의 심각도 (경미, 보통, 심각)"] = "보통",
) -> dict:
    """상황에 맞는 정석 사과문 작성을 위한 system prompt를 생성합니다.

    이 도구는 사용자가 사과문을 작성해야 할 때 호출됩니다.
    반환된 system_prompt를 LLM에게 제공하면, 해당 상황에 맞는
    진정성 있고 효과적인 사과문을 작성하는 데 도움을 받을 수 있습니다.
    """

    severity_guidance = {
        "경미": "간결하면서도 진심이 담긴 사과가 적절합니다.",
        "보통": "구체적인 반성과 함께 개선 의지를 보여주는 사과가 필요합니다.",
        "심각": "깊은 반성, 구체적인 책임 인정, 그리고 명확한 재발 방지 대책을 포함해야 합니다.",
    }

    system_prompt = PROMPT_TEMPLATE.format(
        situation=situation,
        relationship=relationship,
        severity=severity,
        severity_guidance=severity_guidance.get(severity, severity_guidance["보통"]),
    )

    return {
        "system_prompt": system_prompt,
        "usage_guide": "위 가이드라인을 참고하여 상황에 맞는 진정성 있는 사과문을 작성해 주세요."
    }


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

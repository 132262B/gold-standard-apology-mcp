# FastMCP Lambda Boilerplate

AWS Lambda에서 MCP 서버를 실행하기 위한 보일러플레이트 프로젝트

## 아키텍처

```mermaid
flowchart LR
    subgraph Client
        MCP[MCP Client<br/>Claude, etc.]
    end

    subgraph Lambda[AWS Lambda]
        LWA[Lambda Web Adapter<br/>Response Streaming]
        FastMCP[FastMCP 2.0 Server]

        LWA --> FastMCP
    end

    subgraph Endpoints[Endpoints]
        Health["/health<br/>헬스체크"]
        MCP_EP["/mcp<br/>MCP 프로토콜"]
    end

    MCP -->|HTTP/SSE| LWA
    FastMCP --> Health
    FastMCP --> MCP_EP
```

## 동작 원리

### MCP (Model Context Protocol)

MCP는 AI 모델과 외부 도구/데이터 소스를 연결하는 표준 프로토콜입니다.

```mermaid
sequenceDiagram
    participant Client as MCP Client<br/>(Claude Desktop)
    participant Lambda as AWS Lambda
    participant Server as FastMCP Server

    Client->>Lambda: POST /mcp<br/>{"method": "tools/list"}
    Lambda->>Server: HTTP Request
    Server-->>Lambda: Tool 목록 반환
    Lambda-->>Client: SSE Response

    Client->>Lambda: POST /mcp<br/>{"method": "tools/call", "name": "greet"}
    Lambda->>Server: Tool 실행
    Server-->>Lambda: 실행 결과
    Lambda-->>Client: SSE Response
```

### Lambda Web Adapter

AWS Lambda는 기본적으로 이벤트 기반이지만, **Lambda Web Adapter**를 사용하면 일반 HTTP 서버를 Lambda에서 실행할 수 있습니다.

```mermaid
flowchart LR
    subgraph Lambda Runtime
        LWA[Lambda Web Adapter<br/>포트 8080 리스닝]
        APP[FastMCP App<br/>HTTP 서버]
    end

    REQ[HTTP Request] --> LWA
    LWA -->|프록시| APP
    APP -->|Response| LWA
    LWA --> RES[HTTP Response<br/>+ Streaming]
```

**핵심 특징**:
- Lambda Function URL로 직접 HTTP 요청 수신
- Response Streaming으로 SSE(Server-Sent Events) 지원
- 컨테이너 이미지 기반으로 복잡한 의존성 관리 가능

### FastMCP 2.0

FastMCP는 MCP 서버를 쉽게 구축할 수 있는 Python 프레임워크입니다.

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server", stateless_http=True)

@mcp.tool()
async def greet(name: str) -> str:
    """인사말을 반환합니다."""
    return f"Hello, {name}!"
```

**stateless_http=True**: Lambda의 stateless 환경에 맞게 세션 없이 동작

### 요청 처리 흐름

```mermaid
flowchart TB
    subgraph 1. 클라이언트 요청
        A[Claude Desktop] -->|MCP 프로토콜| B[Function URL]
    end

    subgraph 2. Lambda 처리
        B --> C[Lambda Web Adapter]
        C --> D[FastMCP Server]
        D --> E{요청 타입}
        E -->|tools/list| F[등록된 Tool 목록 반환]
        E -->|tools/call| G[Tool 함수 실행]
    end

    subgraph 3. 응답
        F --> H[JSON Response]
        G --> H
        H -->|SSE Stream| A
    end
```

## 기술 스택

| 기술 | 용도 |
|------|------|
| **FastMCP 2.0** | Python MCP 서버 프레임워크 |
| **Lambda Web Adapter** | Lambda에서 HTTP 서버 실행 |
| **Serverless Framework** | Docker 기반 Lambda 배포 |
| **Starlette** | ASGI 웹 프레임워크 |

## 빠른 시작

### 1. 프로젝트 복사

```bash
cp -r fastmcp-lambda-boilerplate my-mcp-server
cd my-mcp-server
```

### 2. 의존성 설치

```bash
# uv 사용 (권장)
uv sync

# 또는 pip
pip install -r requirements.txt
```

### 3. 로컬 실행

```bash
python mcp_server.py
```

### 4. 테스트

```bash
# Health Check
curl http://localhost:8080/health

# Tools List
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

# Tool Call
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "greet", "arguments": {"name": "World"}}}'
```

## AWS Lambda 배포

### 사전 요구사항

#### 1. AWS 계정 및 자격증명

AWS 계정과 IAM 사용자의 Access Key가 필요합니다.

```bash
# AWS CLI 설치 (macOS)
brew install awscli

# AWS 자격증명 설정
aws configure
```

설정 시 필요한 정보:
| 항목 | 설명 | 예시 |
|------|------|------|
| AWS Access Key ID | IAM 사용자 액세스 키 | `AKIAIOSFODNN7EXAMPLE` |
| AWS Secret Access Key | IAM 사용자 시크릿 키 | `wJalrXUtnFEMI/K7MDENG/...` |
| Default region | 배포할 리전 | `ap-northeast-2` |
| Default output format | 출력 형식 | `json` |

> **IAM 권한**: Lambda, API Gateway, CloudFormation, S3, CloudWatch Logs, ECR 권한 필요

#### 2. Docker 설치

Lambda 컨테이너 이미지 빌드에 필요합니다.

```bash
# macOS
brew install --cask docker

# Docker 실행 확인
docker --version
```

#### 3. Node.js 및 Serverless Framework

```bash
# Node.js 설치 (v18 이상 권장)
brew install node

# Serverless Framework 전역 설치
npm install -g serverless

# 프로젝트 의존성 설치
npm install
```

#### 4. Python 환경 (로컬 개발용)

```bash
# uv 설치 (권장)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync

# 또는 pip 사용
pip install -r requirements.txt
```

### 배포

```bash
# 개발 환경 배포
serverless deploy --stage dev

# 프로덕션 배포
serverless deploy --stage prod
```

### 배포 결과

배포 후 Lambda Function URL이 생성됩니다:
- **Endpoint**: `https://{id}.lambda-url.{region}.on.aws/`
- **MCP Endpoint**: `https://{id}.lambda-url.{region}.on.aws/mcp`

## 커스터마이징

### 새로운 Tool 추가

`mcp_server.py`에 새로운 tool 추가:

```python
from typing import Annotated

@mcp.tool()
async def my_tool(
    param1: Annotated[str, "Parameter description"],
    param2: Annotated[int, "Optional parameter"] = 10,
) -> dict:
    """Tool description for MCP clients."""
    # Your logic here
    return {"result": "success"}
```

### 환경 변수 추가

1. `.env` 파일에 변수 추가
2. `serverless.yml`의 `environment` 섹션에 추가:

```yaml
provider:
  environment:
    MY_API_KEY: ${env:MY_API_KEY}
```

### 서버 설정 변경

`mcp_server.py`에서 FastMCP 설정 변경:

```python
mcp = FastMCP(
    name="my-custom-server",
    instructions="Your custom instructions",
    stateless_http=True,
)
```

## 프로젝트 구조

```mermaid
graph TD
    subgraph Core[핵심 파일]
        MCP_SERVER[mcp_server.py<br/>FastMCP 서버 메인]
    end

    subgraph Deploy[배포 설정]
        DOCKER[Dockerfile<br/>Lambda Web Adapter]
        SERVERLESS[serverless.yml<br/>Serverless Framework]
    end

    subgraph Config[설정 파일]
        REQ[requirements.txt<br/>Python 의존성]
        PYPROJECT[pyproject.toml<br/>프로젝트 메타데이터]
        ENV[.env.example<br/>환경변수 템플릿]
    end

    subgraph Meta[메타 파일]
        GITIGNORE[.gitignore]
        README[README.md]
    end

    MCP_SERVER --> DOCKER
    DOCKER --> SERVERLESS
    REQ --> DOCKER
```

## MCP 클라이언트 연결

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://{lambda-url}/mcp",
      "transport": "streamable-http"
    }
  }
}
```

## 주의사항

### ARM Mac에서 빌드 시

Dockerfile에 `--platform=linux/amd64`가 설정되어 있어 ARM Mac에서도 정상적으로 x86_64 이미지가 빌드됩니다.

### Lambda 제한사항

- **Timeout**: 기본 60초 (serverless.yml에서 조정 가능)
- **Memory**: 기본 512MB (serverless.yml에서 조정 가능)
- **Response Streaming**: Lambda Function URL로 활성화됨

### Stateless 모드

`stateless_http=True` 설정으로 Lambda의 stateless 환경에 맞게 동작합니다.

## 문제 해결

### exec format error

Lambda에서 `exec format error` 발생 시:
- Dockerfile의 모든 FROM 문에 `--platform=linux/amd64` 확인
- `serverless.yml`에 `architecture: x86_64` 확인

### Permission denied

Lambda에서 `Permission denied` 발생 시:
- Dockerfile에서 파일 권한 설정 확인
- `COPY --chmod=644` 사용

### Health check 실패

Lambda Web Adapter가 health check 실패 시:
- `/health` 엔드포인트가 `{"status": "ok"}` 반환하는지 확인
- `AWS_LWA_READINESS_CHECK_PATH=/health` 설정 확인
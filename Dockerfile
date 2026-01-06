# FastMCP Lambda Boilerplate
# Uses Lambda Web Adapter for running HTTP servers on AWS Lambda

# Build stage - install dependencies
FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -t /app/packages

# Lambda Web Adapter (explicit platform for ARM Mac compatibility)
FROM --platform=linux/amd64 public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 AS lambda-adapter

# Final stage
FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.12-slim

# Copy Lambda Web Adapter
COPY --from=lambda-adapter /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /app

# Copy installed packages with proper permissions
COPY --from=builder /app/packages /app/packages
RUN chmod -R 755 /app/packages
ENV PYTHONPATH=/app/packages

# Copy application code
COPY --chmod=644 mcp_server.py .
COPY --chmod=644 .env* ./

# Lambda Web Adapter configuration
ENV AWS_LWA_INVOKE_MODE=response_stream
ENV AWS_LWA_READINESS_CHECK_PORT=8080
ENV AWS_LWA_READINESS_CHECK_PATH=/health
ENV PORT=8080

# Run FastMCP server
CMD ["python", "mcp_server.py"]

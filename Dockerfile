FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/aderaaij/mcp-mediastack"
LABEL org.opencontainers.image.description="MCP server for managing a media stack"

WORKDIR /app

RUN pip install --no-cache-dir "mcp[cli]>=1.0.0" "httpx>=0.27.0"

COPY server.py .

EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import socket; s=socket.create_connection(('localhost', 8888), 5)" || exit 1

CMD ["python", "server.py"]

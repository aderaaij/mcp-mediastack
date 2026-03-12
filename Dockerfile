FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/aderaaij/mcp-mediastack"
LABEL org.opencontainers.image.description="MCP server for managing a media stack"

WORKDIR /app

COPY pyproject.toml .
COPY mcp_mediastack/ ./mcp_mediastack/
RUN pip install --no-cache-dir .

EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import socket; s=socket.create_connection(('localhost', 8888), 5)" || exit 1

CMD ["mcp-mediastack"]

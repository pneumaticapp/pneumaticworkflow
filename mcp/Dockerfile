FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable --python /usr/local/bin/python --no-python-downloads

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 MCP_ENABLED=no MCP_PORT=8000
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
RUN useradd --system --uid 10001 --no-create-home mcp
USER 10001
EXPOSE 8000
ENTRYPOINT ["/app/.venv/bin/python", "-m", "pneumatic_mcp"]

FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.14-slim
WORKDIR /app
RUN ln -s /usr/local/bin/python3.14 /usr/sbin/python3.14
COPY --from=builder /app/.venv /app/.venv
COPY . /app
ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-u", "bot.py"]

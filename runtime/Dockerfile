FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm ca-certificates \
    && npm install -g @openai/codex \
    && apt-get purge -y npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY engineering /app/engineering
COPY runtime /app/runtime
COPY AGENTS.md /app/AGENTS.md

CMD ["python", "-m", "http.server", "8080", "--bind", "0.0.0.0"]

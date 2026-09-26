FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm ca-certificates \
    && pip install 'docling>=2,<3' --extra-index-url https://download.pytorch.org/whl/cpu \
    && npm install -g @openai/codex \
    && apt-get purge -y npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY engineering /app/engineering
COPY skills /app/skills
COPY runtime /app/runtime
COPY AGENTS.md /app/AGENTS.md
COPY e2e /app/e2e

RUN python -m compileall -q /app/engineering /app/runtime /app/e2e

EXPOSE 8080
CMD ["python", "-m", "e2e.server"]

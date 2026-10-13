# Single-container build for cloud hosts (Render, Cloud Run, Railway ...).
# For local development with n8n use docker-compose.yml instead.
FROM python:3.12-slim
WORKDIR /srv
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/app ./app
COPY knowledge_base ./knowledge_base
ENV PYTHONUNBUFFERED=1 KB_DIR=/srv/knowledge_base DB_PATH=/tmp/inboxpilot.db DEMO_SEED=1
# Hosts inject $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

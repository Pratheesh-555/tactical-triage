# Try openenv-base first (preferred on HF Spaces).
# Falls back to python:3.11-slim if the image is unavailable locally.
FROM python:3.11-slim

WORKDIR /app

# Copy server dependencies first for layer caching
# Support both local build contexts (root dir) and Hugging Face space context (tactical_triage_env dir)
COPY ./ /app/

# We'll just run pip on requirements if it exists
RUN pip install --no-cache-dir openenv-core && \
    if [ -f "/app/server/requirements.txt" ]; then pip install --no-cache-dir -r /app/server/requirements.txt; fi && \
    if [ -f "/app/requirements.txt" ]; then pip install --no-cache-dir -r /app/requirements.txt; fi

# Environment variable defaults
ENV TACTICAL_TASK=single_incident
ENV PORT=8000
ENV HOST=0.0.0.0
ENV WORKERS=1
ENV PYTHONPATH=/app:/app/server

EXPOSE 8000

CMD uvicorn server.app:app --host $HOST --port $PORT --workers $WORKERS

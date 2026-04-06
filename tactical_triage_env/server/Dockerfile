# Try openenv-base first (preferred on HF Spaces).
# Falls back to python:3.11-slim if the image is unavailable locally.
FROM python:3.11-slim

WORKDIR /app

# Copy server dependencies first for layer caching
COPY server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir openenv-core && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy environment package (models, client, __init__)
COPY tactical_triage_env/ /app/tactical_triage_env/

# Copy server code
COPY server/ /app/server/

# Environment variable defaults
ENV TACTICAL_TASK=single_incident
ENV PORT=8000
ENV HOST=0.0.0.0
ENV WORKERS=1

EXPOSE 8000

CMD uvicorn server.app:app --host $HOST --port $PORT --workers $WORKERS

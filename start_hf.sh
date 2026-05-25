#!/bin/bash
set -e

echo "Starting Qdrant..."
qdrant --config-path /app/qdrant_config.yaml &

QDRANT_PID=$!

cleanup() {
    echo "Shutting down..."
    kill $QDRANT_PID 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Waiting for Qdrant to be ready..."
until curl -sf http://localhost:6333/healthz > /dev/null 2>&1; do
    sleep 1
done
echo "Qdrant is ready."

echo "Starting FastAPI on port 7860..."
exec uvicorn main_api:app --host 0.0.0.0 --port 7860

FROM node:18-alpine AS frontend-build

WORKDIR /app

COPY apps/bookstore-frontend/package*.json ./apps/bookstore-frontend/
RUN cd apps/bookstore-frontend && npm ci

COPY apps/bookstore-frontend ./apps/bookstore-frontend
RUN cd apps/bookstore-frontend && npm run build

FROM python:3.11-slim AS backend

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/apps/bookstore-gateway:/app/apps/bookstore-gateway/shared

COPY apps/bookstore-gateway/requirements.txt /app/apps/bookstore-gateway/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/bookstore-gateway/requirements.txt

COPY apps/bookstore-gateway /app/apps/bookstore-gateway
COPY main.py /app/main.py
COPY --from=frontend-build /app/apps/bookstore-frontend/dist /app/apps/bookstore-frontend/dist

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

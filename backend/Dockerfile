# Orion paper-trading API — Python 3.11, production-oriented image.
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Non-root user for runtime
RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .

RUN chmod +x /app/docker-entrypoint.sh

USER app

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
# Uvicorn with multiple workers can be set via CMD override in orchestration
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

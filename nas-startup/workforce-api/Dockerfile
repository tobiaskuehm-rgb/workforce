FROM python:3.13-alpine

LABEL org.opencontainers.image.title="Start UP Workforce API" \
      org.opencontainers.image.version="v6"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir "fastapi==0.116.1" "pydantic==2.13.4" "uvicorn==0.35.0" "psycopg[binary]==3.2.9" \
    && addgroup -S app \
    && adduser -S -G app app

COPY --chown=app:app app.py /app/app.py

USER app
EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]

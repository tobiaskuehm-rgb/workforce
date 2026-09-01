FROM python:3.13-alpine

LABEL org.opencontainers.image.title="Start UP Workforce API" \
      org.opencontainers.image.version="v8"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir "fastapi==0.116.1" "pydantic==2.13.4" "uvicorn==0.35.0" "psycopg[binary]==3.2.9" \
    # uid and gid are pinned, not left to the base image. The two Docker
    # secrets are bind-mounted host files (measured on the running container),
    # so the host side grants access by number: secrets/ carries group 101 and
    # mode 640. An unpinned adduser happened to produce 100/101 today; the next
    # base image could shift it and the API would lose its own key with a
    # PermissionError at import time (review finding G-044).
    && addgroup -g 101 -S app \
    && adduser -S -G app -u 100 app

COPY --chown=app:app app.py /app/app.py

USER app
EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]

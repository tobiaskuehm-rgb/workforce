FROM python:3.13-alpine

LABEL org.opencontainers.image.title="Start UP Workforce Agent" \
      org.opencontainers.image.version="v1"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir "anthropic==1.2.0" \
    && addgroup -S startup && adduser -S -G startup -u 10001 startup

COPY --chown=startup:startup agent_worker.py bus_client.py data_boundary.py providers.py /app/

USER 10001:10001

CMD ["python", "/app/agent_worker.py"]

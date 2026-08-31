FROM python:3.13-alpine

RUN addgroup -S startup && adduser -S -G startup -u 10001 startup \
    && mkdir -p /var/lib/startup-telegram \
    && chown -R startup:startup /var/lib/startup-telegram

WORKDIR /app
COPY telegram_connector.py /app/telegram_connector.py
COPY identity_probe.py /app/identity_probe.py
COPY network_probe.py /app/network_probe.py

USER 10001:10001

CMD ["python", "/app/telegram_connector.py"]

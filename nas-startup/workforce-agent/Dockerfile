FROM python:3.13-alpine

LABEL org.opencontainers.image.title="Start UP Workforce Agent" \
      org.opencontainers.image.version="v1"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir "anthropic==1.2.0" \
    && addgroup -S startup && adduser -S -G startup -u 10001 startup \
    # The state directory has to exist in the image and belong to the user the
    # container runs as. A named volume mounted onto a path that does not exist
    # in the image is created owned by root, and UID 10001 then cannot open the
    # SQLite file - "unable to open database file" at the first start, found in
    # the chain run on 2026-09-01. The connector image always did this; the
    # agent image did not.
    && mkdir -p /var/lib/startup-agent \
    && chown -R startup:startup /var/lib/startup-agent

COPY --chown=startup:startup agent_worker.py budget.py bus_client.py data_boundary.py efficiency_report.py model_allowlist.py providers.py state_store.py /app/

USER 10001:10001

CMD ["python", "/app/agent_worker.py"]

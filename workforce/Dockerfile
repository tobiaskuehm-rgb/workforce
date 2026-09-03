FROM python:3.13-alpine
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# Standard library only: no pip. Fixed uid/gid so host file rights can name them.
RUN addgroup -S -g 10001 workforce && adduser -S -G workforce -u 10001 workforce \
    && mkdir -p /var/lib/workforce && chown workforce:workforce /var/lib/workforce
WORKDIR /app
COPY --chown=workforce:workforce __init__.py __main__.py app.py boundary.py config.py models.py providers.py store.py telegram.py /app/workforce/
USER 10001:10001
CMD ["python", "-m", "workforce", "run", "--config", "/etc/workforce/config.json"]

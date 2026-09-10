FROM python:3.12.14-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

ARG VCS_REF=""

LABEL org.opencontainers.image.title="Infrastructure Operations Platform" \
    org.opencontainers.image.description="Containerized infrastructure asset management, monitoring, and reporting platform" \
    org.opencontainers.image.version="0.1.0" \
    org.opencontainers.image.source="https://github.com/syawalans/docker-infrastructure-operations-platform" \
    org.opencontainers.image.revision="${VCS_REF}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        iputils-ping \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt /tmp/requirements.txt

RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

RUN groupadd --system appgroup \
    && useradd --system \
        --gid appgroup \
        --home-dir /workspace \
        --shell /usr/sbin/nologin \
        appuser

COPY app /workspace/app

RUN chown -R appuser:appgroup /workspace

USER appuser

EXPOSE 8088

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]

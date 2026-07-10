# Production Dockerfile — foundation scaffold only (no runtime services)
FROM python:3.14-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml requirements.txt ./
COPY models ./models
COPY config ./config
COPY connectors ./connectors
COPY events ./events
COPY versioning ./versioning
COPY audit ./audit
COPY feature_flags ./feature_flags
COPY research ./research
COPY architecture ./architecture
COPY health ./health
COPY metrics ./metrics
COPY platform_logging ./platform_logging
COPY security ./security
COPY notifications ./notifications
COPY monitoring ./monitoring
COPY scripts ./scripts

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD ["python", "scripts/validate_configuration.py"]

CMD ["python", "-c", "print('trading-platform foundation image ready')"]

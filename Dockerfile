# ========== STAGE 1 : Builder ==========
FROM python:3.12-alpine AS builder

# Install build dependencies
RUN apk add --no-cache build-base postgresql-dev

WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv export --format requirements-txt > requirements.txt && \
    pip install --no-cache-dir --prefix=/install --no-compile -r requirements.txt

# ========== STAGE 2 : Production ==========
FROM python:3.12-alpine AS production

# Only the essentials
RUN apk add --no-cache libpq

WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# SURGICAL COPY: Only the site-packages and the binaries
COPY --from=builder /install/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /install/bin /usr/local/bin
COPY --chown=appuser:appgroup src/ ./src/

# ONE SINGLE LAYER for cleanup to ensure space is actually freed
RUN find /usr/local -depth \
    \( \
        \( -type d -a \( -name __pycache__ -o -name test -o -name tests -o -name docs \) \) \
        -o \
        \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name '*.exe' -o -name '*.dist-info' \) \) \
    \) -exec rm -rf '{}' +

USER appuser
EXPOSE 8000

# Simple healthcheck to keep the image light
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
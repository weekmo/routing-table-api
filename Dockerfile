# ============================================
# Stage 1: Builder - Install dependencies
# ============================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy and build dependencies
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -U pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -e .

# ============================================
# Stage 2: Runtime - Minimal production image
# ============================================
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Copy wheels from builder
COPY --from=builder /build/wheels /tmp/wheels

# Install runtime dependencies
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels /tmp/wheels/*.whl && \
    rm -rf /tmp/wheels

# Copy application code
COPY service/ ./service/
COPY routes.txt ./

# Create non-root user
RUN useradd -m -u 1000 apiuser && \
    chown -R apiuser:apiuser /app

USER apiuser

ENV PYTHONUNBUFFERED=1 \
    PROC_NUM=4 \
    HOST=0.0.0.0 \
    PORT=5000

EXPOSE 5000

CMD ["python", "-m", "service"]

# ============================================
# Stage 3: Development - Includes test tools
# ============================================
FROM runtime AS development

USER root

# Install dev dependencies
COPY --from=builder /build /build
RUN pip install --no-cache-dir -e "/build[dev]"

# Copy test files
COPY tests/ ./tests/

USER apiuser

CMD ["pytest", "tests/", "-v"]
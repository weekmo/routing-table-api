FROM python:3.11-slim-bookworm

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e .

# Copy application code
COPY service/ ./service/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PROC_NUM=4 \
    HOST=0.0.0.0 \
    PORT=5000

# Expose the service port
EXPOSE 5000

# Run the service
CMD ["python", "-m", "service"]
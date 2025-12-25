# Stage 1: Builder stage
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install dependencies in a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Final minimal image
FROM python:3.11-slim

# Install only essential runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY bot.py .

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    DATA_PATH=/app/data \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Run as non-root user for security
#RUN useradd -m -u 1000 botuser && \
#    chown -R botuser:botuser /app
#USER botuser

# Run the bot
CMD ["python", "bot.py"]

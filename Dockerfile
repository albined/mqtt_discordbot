FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot.py .

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Set environment variable defaults
ENV DATA_PATH=/app/data

# Run the bot
CMD ["python", "bot.py"]

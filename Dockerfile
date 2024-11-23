# Use Python slim image for a smaller footprint
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy the requirements first for better caching
COPY requirements.txt .

# Install dependencies and basic utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Verify the files are present
RUN ls -la /app && \
    echo "Files copied successfully"

# Command to run your application
CMD ["python", "bot.py"]
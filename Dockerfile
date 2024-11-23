# Use Python slim image for a smaller footprint
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Debug: Print working directory contents before copy
RUN pwd && ls -la

# Copy the requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot file explicitly
COPY bot.py .

# Debug: Print directory contents after copy
RUN echo "Contents of /app after copy:" && \
    ls -la /app && \
    test -f /app/bot.py || echo "bot.py is missing!"

# Command to run your application
CMD ["python", "bot.py"]
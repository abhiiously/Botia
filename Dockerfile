# Use Python slim image for a smaller footprint
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt requirements.txt

# Install git and project dependencies
RUN apt-get update && \
    apt-get install -y git && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Clone the GitHub repository (this will be replaced with your actual repo)
# Note: If your repo is private, you'll need to set up SSH keys or use HTTPS with credentials
ARG GITHUB_REPO
RUN git clone https://github.com/${GITHUB_REPO}.git .

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Command to run your application
CMD ["python", "bot.py"]
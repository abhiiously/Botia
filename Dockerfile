# Use Python slim image for a smaller footprint
FROM python:3.12-slim

# Install git to clone the repository
RUN apt-get update && apt-get install -y git && apt-get clean

# Clone the repository (replace with your GitHub repo URL)
RUN git clone https://github.com/abhiiously/Botia.git /app

# Set working directory
RUN mkdir -p /app
WORKDIR /app
COPY / /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run your application
CMD ["python", "bot.py"]
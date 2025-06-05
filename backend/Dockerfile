# Backend Dockerfile with explicit directory creation and permissions
FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py .

# Create all required data directories with proper permissions
RUN mkdir -p /data/temp /data/vector_db /data/cache /data/db && \
    chmod -R 777 /data

# Set environment variables
ENV STORAGE_PATH=/data
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "app.py"]

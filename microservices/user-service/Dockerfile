FROM python:3.9-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data/db && chmod -R 777 /data

# Expose port
EXPOSE 8001

# Run the application
CMD ["python", "app.py"]

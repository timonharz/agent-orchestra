FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for SSL support
RUN apt-get update && \
    apt-get install -y --no-install-recommends openssl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create certs directory
RUN mkdir -p certs

# Expose the port
EXPOSE 8443

# Set environment variables
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8443

# Run the application
CMD ["python", "server.py"]

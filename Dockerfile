FROM python:3.10-slim

# Install system dependencies including Chrome for Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    python3-tk \
    tk-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (default for Flask/Gunicorn)
EXPOSE 5000

# Start the web server using gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "web_server:app"]

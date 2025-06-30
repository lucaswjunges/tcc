FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \n    apt-get install -y --no-install-recommends \n    gcc \n    python3-dev \n    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose application port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP backend/app.py
ENV FLASK_RUN_PORT 5000

# Entrypoint to run the application
ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]
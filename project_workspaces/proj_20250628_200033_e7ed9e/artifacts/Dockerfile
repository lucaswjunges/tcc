FROM python:3.9-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \n    build-essential \n    libssl-dev \n    libffi-dev \n    libpq-dev \n    nginx \n    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Set environment variables
ARG FLASK_ENV=production
ENV FLASK_ENV=${FLASK_ENV}

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Build frontend (if needed)
# RUN npm install && npm run build

# Final stage for production
FROM python:3.9-alpine

WORKDIR /app

# Install system dependencies for production
RUN apk add --no-cache \n    nginx \n    && addgroup -S nginx \n    && adduser -S -D -h /app nginx

# Copy from builder stage
COPY --from=builder /app /app

# Copy nginx configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Expose application ports
EXPOSE 5000
EXPOSE 80

# Start services in the background
CMD ["sh", "/entrypoint.sh"]

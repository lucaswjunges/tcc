FROM python:3.9-slim

WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install dependencies without caching
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Define environment variables
ENV FLASK_ENV production

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application
CMD ["python", "run.py"]
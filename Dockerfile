# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies (optional but useful)
RUN apt-get update && apt-get install -y curl && apt-get clean

# Copy dependency list (if exists)
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose port
EXPOSE 5000

# Start app using gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]

# Use the official Python image
FROM python:3.9-slim

# Install necessary system dependencies
RUN apt-get update && \
    apt-get install -y libfreetype6-dev libjpeg62-turbo-dev libpng-dev && \
    rm -rf /var/lib/apt/lists/*

# Create directories for fonts
RUN mkdir -p /usr/share/fonts/truetype/arial && \
    mkdir -p /usr/share/fonts/truetype/impact

# Copy the fonts into the image
COPY fonts/arial.ttf /usr/share/fonts/truetype/arial/arial.ttf
COPY fonts/impact.ttf /usr/share/fonts/truetype/impact/impact.ttf

# Copy requirements and install dependencies
COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY app /app
WORKDIR /app

# Expose the application port
EXPOSE 80

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

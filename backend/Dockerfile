FROM python:3.11-slim

# Set workdir inside container
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Expose the port your app runs on
EXPOSE 8000

# Use startup script that runs migrations then starts the server
CMD ["./start.sh"]

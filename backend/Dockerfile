FROM python:3.11-slim

# Set workdir inside container
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port your app runs on
EXPOSE 8000

# Use uvicorn to run the FastAPI app in production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

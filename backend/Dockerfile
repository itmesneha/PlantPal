FROM python:3.11-slim

# Set workdir inside container
WORKDIR /app

# Copy requirements
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy everything from backend/
COPY . .

# Command to run your app
CMD ["python", "app/main.py"]

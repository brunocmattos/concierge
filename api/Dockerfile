# Build our own image for the Concierge API
FROM python:3.12-slim

WORKDIR /app

# Install deps first so this layer is cached when only the code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# 0.0.0.0 makes the API reachable from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
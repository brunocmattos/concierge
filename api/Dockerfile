# Build our own image for the Concierge API
FROM python:3.12-slim

# libgomp1 is needed by onnxruntime (the engine behind the embedding model)
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model INTO the image, so runtime is instant
RUN python -c "from fastembed import TextEmbedding; TextEmbedding()"

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
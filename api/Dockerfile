FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1

WORKDIR /app

# Heavy + stable layer: embedding lib + model download (cached across code/dep changes)
RUN pip install --no-cache-dir fastembed
RUN python -c "from fastembed import TextEmbedding; TextEmbedding()"

# App dependencies (change more often than the model)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
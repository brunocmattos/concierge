import os
import psycopg
from fastapi import FastAPI
from fastembed import TextEmbedding

app = FastAPI(title="Concierge API")
DB_URL = os.environ.get("DATABASE_URL", "postgresql://concierge:concierge@db:5432/concierge")

# Load the embedding model once. Default: BAAI/bge-small-en-v1.5 (384 dims).
# For Portuguese in production, swap to a multilingual model later.
embedder = TextEmbedding()

def embed(text: str) -> str:
    vec = list(embedder.embed([text]))[0].tolist()
    return "[" + ",".join(str(x) for x in vec) + "]"

SEED_DOCS = [
    "To reset your password, click 'Forgot password' on the login page.",
    "Our business hours are Monday to Friday, 9am to 6pm.",
    "You can cancel your subscription in Settings > Billing > Cancel.",
    "Refunds are processed within 5 business days.",
    "To change your billing address, go to Settings > Billing > Address.",
]

@app.get("/health")
def health():
    return {"status": "ok", "service": "concierge"}

@app.post("/seed")
def seed():
    dim = len(list(embedder.embed(["probe"]))[0])
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS knowledge;")
        cur.execute(f"CREATE TABLE knowledge (id serial PRIMARY KEY, content text, embedding vector({dim}));")
        for d in SEED_DOCS:
            cur.execute("INSERT INTO knowledge (content, embedding) VALUES (%s, %s);", (d, embed(d)))
        conn.commit()
    return {"seeded": len(SEED_DOCS), "dim": dim}

@app.get("/search")
def search(q: str, k: int = 3):
    qv = embed(q)
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT content, 1 - (embedding <=> %s::vector) AS score "
            "FROM knowledge ORDER BY embedding <=> %s::vector LIMIT %s;",
            (qv, qv, k),
        )
        rows = cur.fetchall()
    return {"query": q, "results": [{"content": c, "score": round(float(s), 3)} for c, s in rows]}
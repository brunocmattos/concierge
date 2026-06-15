import os
import psycopg
from fastapi import FastAPI

app = FastAPI(title="Concierge API")
DB_URL = os.environ.get("DATABASE_URL", "postgresql://concierge:concierge@db:5432/concierge")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
THRESHOLD = float(os.environ.get("SCORE_THRESHOLD", "0.6"))

SEED_DOCS = [
    "To reset your password, click 'Forgot password' on the login page.",
    "Our business hours are Monday to Friday, 9am to 6pm.",
    "You can cancel your subscription in Settings > Billing > Cancel.",
    "Refunds are processed within 5 business days.",
    "To change your billing address, go to Settings > Billing > Address.",
]

# Heavy deps load only when first used, so importing this module (for tests)
# stays fast and needs neither the model download nor the API key.
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        _embedder = TextEmbedding()
    return _embedder

def embed(text: str) -> str:
    vec = list(get_embedder().embed([text]))[0].tolist()
    return "[" + ",".join(str(x) for x in vec) + "]"

def llm():
    from groq import Groq
    return Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

@app.get("/health")
def health():
    return {"status": "ok", "service": "concierge"}

@app.post("/seed")
def seed():
    dim = len(list(get_embedder().embed(["probe"]))[0])
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

@app.get("/chat")
def chat(q: str):
    qv = embed(q)
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT content, 1 - (embedding <=> %s::vector) AS score "
            "FROM knowledge ORDER BY embedding <=> %s::vector LIMIT 3;",
            (qv, qv),
        )
        rows = cur.fetchall()
    best = float(rows[0][1]) if rows else 0.0
    if best < THRESHOLD:
        return {"handoff": True, "best_score": round(best, 3),
                "answer": "I'm not confident about this one - let me hand you to a human agent."}
    context = "\n".join(f"- {c}" for c, s in rows)
    prompt = ("Answer the question using ONLY the context. "
              "If the context does not contain the answer, say you don't know.\n\n"
              f"Context:\n{context}\n\nQuestion: {q}")
    completion = llm().chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a concise, friendly support assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return {"handoff": False, "best_score": round(best, 3),
            "answer": completion.choices[0].message.content,
            "sources": [c for c, s in rows]}
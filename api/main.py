import os
import psycopg
from fastapi import FastAPI

app = FastAPI(title="Concierge API")

# The host "db" is the compose service name (acts as DNS on the compose network).
DB_URL = os.environ.get("DATABASE_URL", "postgresql://concierge:concierge@db:5432/concierge")

@app.get("/health")
def health():
    return {"status": "ok", "service": "concierge"}

@app.get("/db-check")
def db_check():
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM knowledge;")
            count = cur.fetchone()[0]
    return {"db": "connected", "knowledge_rows": count}
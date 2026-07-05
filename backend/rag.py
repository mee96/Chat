"""rag.py — Recuperació (retrieval) per al xat de gramàtica: cerca a Qdrant.

Els embeddings (ingesta i query) usen el mateix model via fastembed (ONNX, sense
torch), de manera que els vectors són compatibles. El client de Qdrant i el model
s'inicialitzen de forma lazy (una sola vegada) amb QDRANT_URL/QDRANT_API_KEY del .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastembed import TextEmbedding
from qdrant_client import QdrantClient

# Carrega backend/.env perquè get_client() trobi QDRANT_URL/QDRANT_API_KEY encara
# que rag.py s'usi de forma independent (p. ex. des d'ingest_pdf.py, que no passa
# per main.py). Sense això, QDRANT_URL seria None i QdrantClient cauria a
# localhost:6333 (→ WinError 10061). Les variables ja definides a l'entorn (p. ex.
# a Render) tenen prioritat.
load_dotenv(Path(__file__).resolve().parent / ".env")

COLLECTION = "gramatica"
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_SIZE = 384

_model: TextEmbedding | None = None
_client: QdrantClient | None = None


def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=EMBED_MODEL)
    return _model


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        # timeout ample (per defecte 120s) perquè els upserts grossos de la ingesta
        # no es tallin amb ReadTimeout; configurable amb QDRANT_TIMEOUT.
        _client = QdrantClient(
            url=os.environ.get("QDRANT_URL"),
            api_key=os.environ.get("QDRANT_API_KEY"),
            timeout=int(os.environ.get("QDRANT_TIMEOUT", "120")),
        )
    return _client


def embed_one(text: str) -> list[float]:
    return list(get_model().embed([text]))[0].tolist()


def search(query: str, top_k: int = 3) -> list[str]:
    vector = embed_one(query)
    result = get_client().query_points(
        collection_name=COLLECTION, query=vector, limit=top_k
    )
    return [point.payload["text"] for point in result.points]

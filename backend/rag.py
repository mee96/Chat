"""rag.py — Recuperació (retrieval) per al xat de gramàtica: cerca a Qdrant.

Els embeddings (ingesta i query) es generen al servidor amb Qdrant Cloud
Inference (cloud_inference=True): el procés de Render mai carrega cap model
en local, evitant l'OOM del pla gratuït (512Mi) que fastembed provocava. El
client de Qdrant s'inicialitza de forma lazy (una sola vegada) amb
QDRANT_URL/QDRANT_API_KEY del .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Document

# Carrega backend/.env perquè get_client() trobi QDRANT_URL/QDRANT_API_KEY encara
# que rag.py s'usi de forma independent (p. ex. des d'ingest_pdf.py, que no passa
# per main.py). Sense això, QDRANT_URL seria None i QdrantClient cauria a
# localhost:6333 (→ WinError 10061). Les variables ja definides a l'entorn (p. ex.
# a Render) tenen prioritat.
load_dotenv(Path(__file__).resolve().parent / ".env")

COLLECTION = "gramatica"
EMBED_MODEL = "intfloat/multilingual-e5-small"
VECTOR_SIZE = 384

# Llindar de score sota el qual es descarta un resultat. Calibrat amb proves
# reals sobre aquest corpus concret: preguntes dins del temari ~0.86-0.88,
# preguntes relacionades però absents del corpus ~0.84-0.86, preguntes
# clarament irrellevants ~0.77-0.82. 0.82 talla només aquest darrer grup.
#
# Aquest valor NO és el 0.70 del portfolio (Bunsen) ni s'hi ha de copiar
# directament: la banda de scores E5 depèn del corpus, no del model. Textos
# densos de gramàtica en castellà (com aquest) donen scores globalment més
# alts que el corpus curt i variat del portfolio; calibrar-ho de nou amb
# preguntes reals sobre el corpus concret cada cop que es canviï.
SCORE_THRESHOLD = 0.82

_client: QdrantClient | None = None


def query_document(text: str) -> Document:
    # Aplicat manualment perquè Qdrant Cloud Inference encara no afegeix els
    # prefixos query:/passage: que la família E5 necessita
    # (github.com/qdrant/qdrant/issues/9024, obert a 2026-08) — sense el
    # prefix, incrusta el text literal i la qualitat de cerca es degrada en
    # silenci.
    return Document(text=f"query: {text}", model=EMBED_MODEL)


def passage_document(text: str) -> Document:
    return Document(text=f"passage: {text}", model=EMBED_MODEL)


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        # timeout ample (per defecte 120s) perquè els upserts grossos de la ingesta
        # no es tallin amb ReadTimeout; configurable amb QDRANT_TIMEOUT.
        # port=None: si la QDRANT_URL no porta port, el client afegiria :6333 per
        # defecte; amb None respecta l'HTTPS estàndard (443) del Qdrant Cloud (i
        # si la URL sí porta port explícit, es continua respectant).
        _client = QdrantClient(
            url=os.environ.get("QDRANT_URL"),
            api_key=os.environ.get("QDRANT_API_KEY"),
            port=None,
            timeout=int(os.environ.get("QDRANT_TIMEOUT", "120")),
            cloud_inference=True,
        )
    return _client


def search(query: str, top_k: int = 2, threshold: float = SCORE_THRESHOLD) -> list[str]:
    result = get_client().query_points(
        collection_name=COLLECTION,
        query=query_document(query),
        limit=top_k,
    )
    return [point.payload["text"] for point in result.points if point.score >= threshold]

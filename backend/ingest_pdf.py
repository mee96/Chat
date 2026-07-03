"""ingest_pdf.py — Ingesta offline dels PDFs cap a Qdrant (s'executa en local).

Llegeix els PDFs de backend/pdfs/, els parteix en chunks, genera embeddings amb
fastembed (mateix model que la cerca) i els indexa a la col·lecció de Qdrant.
NO s'executa a Render. Ús:  python ingest_pdf.py [ruta1.pdf ruta2.pdf ...]
"""

import glob
import os
import sys

import pdfplumber
from qdrant_client.models import Distance, PointStruct, VectorParams

from rag import COLLECTION, VECTOR_SIZE, get_client, get_model

PDF_DIR = os.path.join(os.path.dirname(__file__), "pdfs")


def chunk_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    """Parteix `text` en chunks de ~`size` paraules amb `overlap` de solapament."""
    words = text.split()
    if not words:
        return []
    step = max(size - overlap, 1)
    chunks: list[str] = []
    for start in range(0, len(words), step):
        chunk = words[start:start + size]
        if chunk:
            chunks.append(" ".join(chunk))
        if start + size >= len(words):
            break
    return chunks


def main() -> None:
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    if not paths:
        print(f"No s'han trobat PDFs a {PDF_DIR}")
        return

    model = get_model()
    client = get_client()
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )

    point_id = 0
    total_pages = 0
    total_chunks = 0
    for path in paths:
        source = os.path.basename(path)
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                total_pages += 1
                chunks = chunk_text(page.extract_text() or "")
                if not chunks:
                    continue
                vectors = list(model.embed(chunks))
                points = []
                for chunk, vec in zip(chunks, vectors):
                    points.append(PointStruct(
                        id=point_id,
                        vector=vec.tolist(),
                        payload={"text": chunk, "source": source, "page": page_num},
                    ))
                    point_id += 1
                    total_chunks += 1
                client.upsert(COLLECTION, points=points)
        print(f"Indexat: {source}")

    print(f"Fitxers: {len(paths)} | pàgines: {total_pages} | chunks: {total_chunks}")


if __name__ == "__main__":
    main()

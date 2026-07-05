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
        print(f"No s'han trobat PDFs a {PDF_DIR}", flush=True)
        return
    print(f"PDFs a processar ({len(paths)}): {[os.path.basename(p) for p in paths]}", flush=True)

    print("Carregant el model d'embeddings (la primera vegada el descarrega, ~120 MB)...", flush=True)
    model = get_model()
    print("Model carregat.", flush=True)

    print("Connectant a Qdrant...", flush=True)
    client = get_client()
    if not client.collection_exists(COLLECTION):
        print(f"Creant la col·lecció '{COLLECTION}' (size={VECTOR_SIZE}, cosinus)...", flush=True)
        client.create_collection(
            COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    else:
        print(f"La col·lecció '{COLLECTION}' ja existeix.", flush=True)

    point_id = 0
    total_pages = 0
    total_chunks = 0
    for path in paths:
        source = os.path.basename(path)
        print(f"\n=== {source} ===", flush=True)
        with pdfplumber.open(path) as pdf:
            num_pages = len(pdf.pages)
            print(f"  {num_pages} pàgines", flush=True)
            for page_num, page in enumerate(pdf.pages, start=1):
                total_pages += 1
                chunks = chunk_text(page.extract_text() or "")
                if not chunks:
                    print(f"  pàg {page_num}/{num_pages}: 0 chunks (saltada)", flush=True)
                    continue
                print(f"  pàg {page_num}/{num_pages}: {len(chunks)} chunks — generant embeddings...", flush=True)
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
                print(f"  pàg {page_num}/{num_pages}: pujant {len(points)} punts a Qdrant...", flush=True)
                client.upsert(COLLECTION, points=points)
        print(f"Indexat: {source} (chunks acumulats: {total_chunks})", flush=True)

    print(f"\nFet. Fitxers: {len(paths)} | pàgines: {total_pages} | chunks: {total_chunks}", flush=True)


if __name__ == "__main__":
    main()

"""ingest_pdf.py — Ingesta offline dels PDFs cap a Qdrant (s'executa en local).

Llegeix els PDFs de backend/pdfs/, els parteix en chunks i els indexa a la
col·lecció de Qdrant. Els embeddings es generen al servidor amb Qdrant Cloud
Inference (mateix model que la cerca a rag.py), sense carregar cap model en
local. NO s'executa a Render. Ús:  python ingest_pdf.py [ruta1.pdf ruta2.pdf ...]
"""

import glob
import os
import re
import sys
import time
import uuid

import pdfplumber
from qdrant_client.models import Distance, PointStruct, VectorParams

from rag import COLLECTION, VECTOR_SIZE, get_client, passage_document

PDF_DIR = os.path.join(os.path.dirname(__file__), "pdfs")

# Namespace fix per generar ids de punt deterministes: re-executar la ingesta
# torna a produir els mateixos ids, així l'upsert és idempotent (sobreescriu en
# lloc de duplicar) i es pot reprendre amb seguretat.
_ID_NAMESPACE = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")


def point_id_for(source: str, page: int, chunk_idx: int) -> str:
    """Id determinista d'un chunk a partir de (font, pàgina, índex dins la pàgina)."""
    return str(uuid.uuid5(_ID_NAMESPACE, f"{source}#{page}#{chunk_idx}"))


def indexed_pages(client, collection: str) -> set[tuple[str, int]]:
    """Retorna el conjunt de (source, page) que ja tenen punts a la col·lecció.

    Recorre tota la col·lecció amb scroll paginat perquè main() pugui saltar les
    pàgines ja indexades i reprendre des d'on es va quedar.
    """
    done: set[tuple[str, int]] = set()
    offset = None
    while True:
        records, offset = client.scroll(
            collection_name=collection,
            limit=1000,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for record in records:
            done.add((record.payload["source"], record.payload["page"]))
        if offset is None:
            break
    return done


def upsert_with_retry(
    client, collection: str, points, retries: int = 5, base_delay: float = 2.0
) -> None:
    """Fa upsert reintentant amb backoff exponencial davant errors transitoris
    (p. ex. ReadTimeout de Qdrant). Reeleva l'excepció si s'esgoten els intents."""
    for attempt in range(1, retries + 1):
        try:
            client.upsert(collection, points=points)
            return
        except Exception as exc:  # noqa: BLE001 — script offline: reintenta qualsevol error de xarxa
            if attempt == retries:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            print(
                f"    upsert ha fallat ({type(exc).__name__}: {exc}); "
                f"reintent {attempt}/{retries - 1} d'aquí {delay:.0f}s...",
                flush=True,
            )
            time.sleep(delay)


_BIBLIO_HEADER_RE = re.compile(r"referencias\s+bibliogr[aá]ficas", re.IGNORECASE)


def is_bibliography_page(text: str) -> bool:
    """Detecta pàgines de bibliografia/referències (capçalera "Referencias
    bibliográficas" repetida a totes les pàgines de l'apartat). Es descarten
    perquè mai contenen explicacions de gramàtica i, amb els embeddings E5,
    poden puntuar més alt que contingut rellevant real (falsos positius al
    retrieval — vist en producció amb preguntes sobre el subjuntiu)."""
    return bool(_BIBLIO_HEADER_RE.search(text[:80]))


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

    print("Connectant a Qdrant...", flush=True)
    client = get_client()
    if not client.collection_exists(COLLECTION):
        print(f"Creant la col·lecció '{COLLECTION}' (size={VECTOR_SIZE}, cosinus)...", flush=True)
        client.create_collection(
            COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        done = set()
    else:
        print(f"La col·lecció '{COLLECTION}' ja existeix; comprovant què ja hi ha indexat...", flush=True)
        done = indexed_pages(client, COLLECTION)
        print(f"  {len(done)} pàgines ja indexades (es saltaran per reprendre).", flush=True)

    total_pages = 0
    total_chunks = 0
    skipped_pages = 0
    for path in paths:
        source = os.path.basename(path)
        print(f"\n=== {source} ===", flush=True)
        with pdfplumber.open(path) as pdf:
            num_pages = len(pdf.pages)
            print(f"  {num_pages} pàgines", flush=True)
            for page_num, page in enumerate(pdf.pages, start=1):
                total_pages += 1
                if (source, page_num) in done:
                    skipped_pages += 1
                    print(f"  pàg {page_num}/{num_pages}: ja indexada (saltada)", flush=True)
                    continue
                text = page.extract_text() or ""
                if is_bibliography_page(text):
                    print(f"  pàg {page_num}/{num_pages}: bibliografia (saltada)", flush=True)
                    continue
                chunks = chunk_text(text)
                if not chunks:
                    print(f"  pàg {page_num}/{num_pages}: 0 chunks (saltada)", flush=True)
                    continue
                print(f"  pàg {page_num}/{num_pages}: {len(chunks)} chunks", flush=True)
                points = []
                for chunk_idx, chunk in enumerate(chunks):
                    points.append(PointStruct(
                        id=point_id_for(source, page_num, chunk_idx),
                        vector=passage_document(chunk),
                        payload={"text": chunk, "source": source, "page": page_num},
                    ))
                    total_chunks += 1
                print(f"  pàg {page_num}/{num_pages}: pujant {len(points)} punts a Qdrant...", flush=True)
                upsert_with_retry(client, COLLECTION, points)
        print(f"Indexat: {source} (chunks nous acumulats: {total_chunks})", flush=True)

    print(
        f"\nFet. Fitxers: {len(paths)} | pàgines vistes: {total_pages} "
        f"| ja indexades (saltades): {skipped_pages} | chunks nous: {total_chunks}",
        flush=True,
    )


if __name__ == "__main__":
    main()

"""
ingest_pdf.py — Script d'ingesta del PDF cap a Qdrant (infraestructura preparatòria).

BUIT DE MOMENT. Aquest script s'executarà UN COP (o cada vegada que canviï el PDF)
per processar el document i pujar-lo a la col·lecció de Qdrant. La consulta en temps
real (retrieval) viurà a rag.py; això és només la part d'indexat offline.

Ús previst (quan estigui implementat)
-------------------------------------
    python ingest_pdf.py <ruta_al_pdf>

Passos previstos (reutilitzant les funcions de rag.py)
------------------------------------------------------
1) Llegir la ruta del PDF dels arguments (sys.argv) o d'una constant/env.
2) load_pdf(path)      — extreure el text del PDF.
3) chunk_text(...)     — partir en chunks amb solapament.
4) embed(...)          — generar els embeddings dels chunks.
5) index_chunks(...)   — crear la col·lecció a Qdrant (si cal) i fer upsert.
6) Mostrar un resum (nombre de pàgines, de chunks i de vectors indexats).

Nota: aquest fitxer NO s'importa des de main.py; és una eina de línia de comandes
independent per preparar l'índex vectorial.
"""

# TODO: implementar la ingesta reutilitzant les funcions de rag.py.

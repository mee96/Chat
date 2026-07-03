"""
rag.py — Chatbot RAG amb PDF + Qdrant (infraestructura preparatòria).

BUIT DE MOMENT. Aquest mòdul contindrà la lògica de recuperació (retrieval)
que alimentarà la Yuki amb context extret d'un PDF. Aquí sota hi ha l'estructura
prevista del pipeline; s'implementarà més endavant.

Dependències previstes: pdfplumber (extracció de text del PDF),
sentence-transformers (embeddings), qdrant-client (base de dades vectorial).

Estructura prevista
-------------------

1) Configuració
   - Nom de la col·lecció de Qdrant.
   - Model d'embeddings (p. ex. sentence-transformers "all-MiniLM-L6-v2").
   - Connexió al client de Qdrant (local o servidor / Qdrant Cloud).
   - Mida del chunk i solapament (overlap).

2) Càrrega del PDF
   - Obrir el PDF amb pdfplumber i extreure el text pàgina a pàgina.
   - Retornar el text (o una llista de (pàgina, text)) per al chunking.

3) Chunking
   - Partir el text en fragments (chunks) de mida controlada, amb solapament,
     per no trencar el context a mig concepte.
   - Cada chunk guardarà metadades (p. ex. número de pàgina, índex del chunk).

4) Embeddings
   - Carregar el model de sentence-transformers un sol cop (cache).
   - Convertir cada chunk en un vector d'embedding.

5) Indexat a Qdrant
   - Crear la col·lecció si no existeix (dimensió = mida de l'embedding,
     distància = cosinus).
   - Fer upsert dels vectors amb el seu payload (text del chunk + metadades).

6) Cerca per query (retrieval)
   - Funció que, donada una consulta de l'usuari:
       a) genera l'embedding de la query,
       b) fa una cerca top-k a Qdrant,
       c) retorna els chunks més rellevants (text + metadades + score),
     perquè s'injectin com a context al prompt de la Yuki.

Interfícies previstes (encara no implementades)
-----------------------------------------------
- load_pdf(path) -> text / llista de fragments
- chunk_text(text, chunk_size, overlap) -> list[chunk]
- embed(texts) -> list[vector]
- index_chunks(chunks) -> None            # crea col·lecció + upsert
- search(query, top_k) -> list[resultat]  # retrieval per a la Yuki
"""

# TODO: implementar el pipeline descrit a dalt quan tinguem el PDF i Qdrant a punt.

import ingest_pdf


def test_chunk_text_size_and_overlap():
    words = [f"w{i}" for i in range(1000)]
    text = " ".join(words)
    chunks = ingest_pdf.chunk_text(text, size=500, overlap=50)
    # step = 500 - 50 = 450 -> inicis 0, 450, 900
    assert len(chunks) == 3
    assert chunks[0].split()[0] == "w0"
    assert len(chunks[0].split()) == 500
    assert chunks[1].split()[0] == "w450"   # solapament de 50 amb l'anterior
    assert chunks[2].split()[0] == "w900"
    assert len(chunks[2].split()) == 100     # últim chunk més curt


def test_chunk_text_short_text_single_chunk():
    chunks = ingest_pdf.chunk_text("una dos tres", size=500, overlap=50)
    assert chunks == ["una dos tres"]


def test_chunk_text_empty():
    assert ingest_pdf.chunk_text("") == []

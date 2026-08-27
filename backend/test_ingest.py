import pytest

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


def test_is_bibliography_page_detects_header_variants():
    assert ingest_pdf.is_bibliography_page("Referencias bibliográficas 1572 REFERENCIAS...")
    assert ingest_pdf.is_bibliography_page("1573 Referencias bibliográficas Gómez López...")
    assert ingest_pdf.is_bibliography_page("REFERENCIAS BIBLIOGRÁFICAS Alarcos Llorach...")


def test_is_bibliography_page_ignores_regular_content():
    assert not ingest_pdf.is_bibliography_page("El modo subjuntivo se emplea para expresar...")
    assert not ingest_pdf.is_bibliography_page("")


def test_point_id_deterministic_and_unique():
    # Mateixa (font, pàgina, índex) -> mateix id (idempotència en re-executar).
    a = ingest_pdf.point_id_for("a.pdf", 1, 0)
    assert a == ingest_pdf.point_id_for("a.pdf", 1, 0)
    # Qualsevol component diferent -> id diferent.
    assert a != ingest_pdf.point_id_for("a.pdf", 1, 1)
    assert a != ingest_pdf.point_id_for("a.pdf", 2, 0)
    assert a != ingest_pdf.point_id_for("b.pdf", 1, 0)


def test_indexed_pages_scrolls_all_and_collects_source_page():
    class Rec:
        def __init__(self, source, page):
            self.payload = {"source": source, "page": page}

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def scroll(self, collection_name, limit, offset, with_payload, with_vectors):
            assert collection_name == "gramatica"
            assert with_vectors is False
            self.calls += 1
            if self.calls == 1:
                assert offset is None
                return ([Rec("a.pdf", 1), Rec("a.pdf", 2)], "cursor")
            assert offset == "cursor"
            return ([Rec("b.pdf", 1)], None)

    client = FakeClient()
    done = ingest_pdf.indexed_pages(client, "gramatica")
    assert done == {("a.pdf", 1), ("a.pdf", 2), ("b.pdf", 1)}
    assert client.calls == 2


def test_upsert_with_retry_succeeds_after_transient_failures(monkeypatch):
    monkeypatch.setattr(ingest_pdf.time, "sleep", lambda _s: None)

    class FakeClient:
        def __init__(self):
            self.attempts = 0

        def upsert(self, collection, points):
            self.attempts += 1
            if self.attempts < 3:
                raise RuntimeError("timeout")
            return "ok"

    client = FakeClient()
    ingest_pdf.upsert_with_retry(client, "gramatica", [1, 2], retries=5, base_delay=0.01)
    assert client.attempts == 3


def test_upsert_with_retry_raises_after_exhausting(monkeypatch):
    monkeypatch.setattr(ingest_pdf.time, "sleep", lambda _s: None)

    class FakeClient:
        def __init__(self):
            self.attempts = 0

        def upsert(self, collection, points):
            self.attempts += 1
            raise RuntimeError("always down")

    client = FakeClient()
    with pytest.raises(RuntimeError):
        ingest_pdf.upsert_with_retry(client, "gramatica", [1], retries=3, base_delay=0.01)
    assert client.attempts == 3

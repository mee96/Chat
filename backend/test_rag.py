import rag


def test_search_returns_chunk_texts_above_threshold(monkeypatch):
    class FakePoint:
        def __init__(self, text, score):
            self.payload = {"text": text}
            self.score = score

    class FakeResult:
        points = [FakePoint("chunk A", 0.90), FakePoint("chunk B", 0.75)]

    class FakeClient:
        def query_points(self, collection_name, query, limit):
            assert collection_name == rag.COLLECTION
            assert limit == 3
            assert query.text == "query: com es fa el plural?"
            assert query.model == rag.EMBED_MODEL
            return FakeResult()

    monkeypatch.setattr(rag, "get_client", lambda: FakeClient())

    assert rag.search("com es fa el plural?", top_k=3) == ["chunk A", "chunk B"]


def test_search_filters_out_scores_below_threshold(monkeypatch):
    class FakePoint:
        def __init__(self, text, score):
            self.payload = {"text": text}
            self.score = score

    class FakeResult:
        points = [FakePoint("chunk A", 0.90), FakePoint("chunk B", 0.50)]

    class FakeClient:
        def query_points(self, collection_name, query, limit):
            return FakeResult()

    monkeypatch.setattr(rag, "get_client", lambda: FakeClient())

    assert rag.search("una pregunta", threshold=0.70) == ["chunk A"]


def test_search_default_top_k_is_two(monkeypatch):
    # Menys context per petició (413 al pla gratuït de Groq).
    captured = {}

    class FakeResult:
        points = []

    class FakeClient:
        def query_points(self, collection_name, query, limit):
            captured["limit"] = limit
            return FakeResult()

    monkeypatch.setattr(rag, "get_client", lambda: FakeClient())

    rag.search("una pregunta")
    assert captured["limit"] == 2


def test_query_document_applies_query_prefix():
    doc = rag.query_document("com es fa el plural?")
    assert doc.text == "query: com es fa el plural?"
    assert doc.model == rag.EMBED_MODEL


def test_passage_document_applies_passage_prefix():
    doc = rag.passage_document("El plural es forma afegint -s.")
    assert doc.text == "passage: El plural es forma afegint -s."
    assert doc.model == rag.EMBED_MODEL


def test_get_client_passes_timeout_from_env(monkeypatch):
    monkeypatch.setattr(rag, "_client", None)
    monkeypatch.setenv("QDRANT_TIMEOUT", "77")
    captured = {}

    class FakeQdrantClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(rag, "QdrantClient", FakeQdrantClient)

    rag.get_client()
    assert captured["timeout"] == 77


def test_get_client_timeout_defaults_when_env_absent(monkeypatch):
    monkeypatch.setattr(rag, "_client", None)
    monkeypatch.delenv("QDRANT_TIMEOUT", raising=False)
    captured = {}

    class FakeQdrantClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(rag, "QdrantClient", FakeQdrantClient)

    rag.get_client()
    assert captured["timeout"] == 120


def test_get_client_does_not_force_default_port(monkeypatch):
    # Qdrant Cloud usa HTTPS (443). Passar port=None evita que el client afegeixi
    # el :6333 per defecte quan la QDRANT_URL no porta port explícit.
    monkeypatch.setattr(rag, "_client", None)
    captured = {}

    class FakeQdrantClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(rag, "QdrantClient", FakeQdrantClient)

    rag.get_client()
    assert captured["port"] is None


def test_get_client_enables_cloud_inference(monkeypatch):
    monkeypatch.setattr(rag, "_client", None)
    captured = {}

    class FakeQdrantClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(rag, "QdrantClient", FakeQdrantClient)

    rag.get_client()
    assert captured["cloud_inference"] is True

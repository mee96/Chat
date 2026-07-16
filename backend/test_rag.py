import rag


def test_search_returns_chunk_texts_in_order(monkeypatch):
    monkeypatch.setattr(rag, "embed_one", lambda q: [0.0] * rag.VECTOR_SIZE)

    class FakePoint:
        def __init__(self, text):
            self.payload = {"text": text}

    class FakeResult:
        points = [FakePoint("chunk A"), FakePoint("chunk B")]

    class FakeClient:
        def query_points(self, collection_name, query, limit):
            assert collection_name == rag.COLLECTION
            assert limit == 3
            assert query == [0.0] * rag.VECTOR_SIZE
            return FakeResult()

    monkeypatch.setattr(rag, "get_client", lambda: FakeClient())

    assert rag.search("com es fa el plural?", top_k=3) == ["chunk A", "chunk B"]


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

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

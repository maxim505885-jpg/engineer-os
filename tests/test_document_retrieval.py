from engineering.document_intelligence import DocumentChunk, EvidenceContextCatalog


def test_evidence_context_retrieval_is_deterministic() -> None:
    chunks = (
        DocumentChunk("doc:chunk:0001", "doc", 1, "колонна бетон арматура", ("doc:paragraph:0001",), ("paragraph",)),
        DocumentChunk("doc:chunk:0002", "doc", 2, "кровля ферма сталь", ("doc:paragraph:0002",), ("paragraph",)),
    )
    catalog = EvidenceContextCatalog()
    catalog.register("doc", chunks)

    result = catalog.retrieve(("doc",), "проверить колонну и арматуру", limit=1)

    assert [chunk.id for chunk in result] == ["doc:chunk:0001"]
    assert catalog.evidence_ids(("doc",), ("doc:chunk:0001",)) == ("doc:paragraph:0001",)


def test_evidence_context_never_returns_unregistered_material() -> None:
    catalog = EvidenceContextCatalog()
    catalog.register("doc", ())

    assert catalog.retrieve(("missing",), "колонна", limit=8) == ()

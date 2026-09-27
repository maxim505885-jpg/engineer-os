"""Deterministic A/B evaluation for untrusted document retrieval providers."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import NormalizedDocument
from .retrieval_adapters import RetrievalHit


@dataclass(frozen=True)
class RetrievalBenchmarkCase:
    query: str
    expected_block_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("benchmark query is required")
        if not self.expected_block_ids:
            raise ValueError("benchmark requires confirmed expected blocks")
        if len(set(self.expected_block_ids)) != len(self.expected_block_ids):
            raise ValueError("expected block IDs must be unique")


@dataclass(frozen=True)
class RetrievalBenchmarkResult:
    provider: str
    cases: int
    exact_top1: int
    expected_recall_hits: int
    expected_recall_total: int

    @property
    def top1_rate(self) -> float:
        return self.exact_top1 / self.cases if self.cases else 0.0

    @property
    def expected_recall(self) -> float:
        return self.expected_recall_hits / self.expected_recall_total if self.expected_recall_total else 0.0


def benchmark_retriever(
    provider: str,
    document: NormalizedDocument,
    cases: tuple[RetrievalBenchmarkCase, ...],
    retrieve,
) -> RetrievalBenchmarkResult:
    if not provider.strip():
        raise ValueError("provider is required")
    if not cases:
        raise ValueError("at least one benchmark case is required")

    known = {block.block_id for block in document.blocks}
    exact_top1 = 0
    recall_hits = 0
    recall_total = 0

    for case in cases:
        unknown_expected = set(case.expected_block_ids) - known
        if unknown_expected:
            raise ValueError("benchmark expected block is not in normalized document")

        hits = tuple(retrieve(document, case.query))
        if not hits:
            raise ValueError("retriever returned no hits")
        if any(not isinstance(hit, RetrievalHit) or hit.block_id not in known for hit in hits):
            raise ValueError("retriever returned an invalid or unknown block")

        returned = tuple(hit.block_id for hit in hits)
        if returned[0] in case.expected_block_ids:
            exact_top1 += 1
        recall_hits += len(set(returned) & set(case.expected_block_ids))
        recall_total += len(case.expected_block_ids)

    return RetrievalBenchmarkResult(
        provider=provider,
        cases=len(cases),
        exact_top1=exact_top1,
        expected_recall_hits=recall_hits,
        expected_recall_total=recall_total,
    )

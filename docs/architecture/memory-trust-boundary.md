# Memory trust boundary

External memory (for example Mem0) is contextual recall, not engineering evidence.

- Default trust is UNVERIFIED.
- CONFIRMED_REFERENCE means a user/system-confirmed reusable reference; it still
  has evidentiary_status=NOT_EVIDENCE in a new task.
- Every record requires a source_ref.
- Memory cannot emit AgentResult, EvidenceCandidate, PASS or ACCEPTED.
- A remembered statement must be re-established from current task evidence before
  it can participate in an engineering conclusion.
- Duplicate or malformed backend records fail closed.

This allows ENGINEER OS to learn workflows and preferences without treating
model memory as factual inspection data.

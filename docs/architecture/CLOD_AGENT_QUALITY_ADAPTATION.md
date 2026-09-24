# Clod- → ENGINEER OS: Agent Quality Adaptation

This document records the first controlled adaptation of useful Clod-/ECC
ideas into ENGINEER OS. It is intentionally narrow.

## Scope

Adapted:

- deterministic Agent Harness;
- regression scenarios with explicit expected/forbidden statuses;
- evidence and certainty gates;
- fail-closed behavior when the existing Result Validator rejects a result.

Not adapted:

- Clod-/Claude runtime;
- Clod- Codex or Hermes configuration;
- coding-specific reviewer agents;
- LLM self-scoring;
- hidden repair loops.

## Boundary

The quality layer does not decide engineering truth.

The authoritative flow remains:

INPUT → Document Intelligence → Evidence → Engineer Core → Agent Result
→ Result Validator → independent verification (when implemented)
→ FINAL AUDIT.

The harness is a regression and contract layer around this flow.

## Safety rules

1. UNCERTAINTY is not converted to acceptance.
2. Forbidden accepting statuses fail a regression case.
3. Evidence is validated by the existing Result Validator.
4. The harness never invents evidence, measurements, calculations, normative
   requirements, or engineering conclusions.
5. A semantic independent verifier is intentionally not implemented yet; this
   first step only creates the deterministic contract boundary.

## Future extension

A later independent-verification stage may consume an agent finding and return
CONFIRMED, REFUTED, or UNCERTAIN. It must be evidence-backed and must not
clear an unresolved blocker merely because the verifier is uncertain.

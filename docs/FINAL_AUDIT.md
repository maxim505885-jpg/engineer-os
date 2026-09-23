# FINAL_AUDIT Contract

A deliverable may receive FINAL_AUDIT only after the following checks pass.

## Required checks

- [ ] ТЗ requirements identified and addressed.
- [ ] Object and scope are identified.
- [ ] Evidence is traceable.
- [ ] Facts are separated from assumptions and interpretations.
- [ ] Defects are supported by evidence.
- [ ] Causes/mechanisms are not asserted beyond evidence.
- [ ] Normative references are applicable and edition-aware.
- [ ] Calculations are independently verified or clearly marked as unverified.
- [ ] Conclusions do not exceed the available evidence.
- [ ] No invented measurements, test results, clauses, calculations, or source facts.
- [ ] No unresolved ERROR or BLOCK.
- [ ] Remaining WARNING/UNCERTAINTY items are explicitly disclosed.
- [ ] Changes are traceable.

## Decision rule

FINAL_AUDIT is a verification state, not a quality score.

If evidence is insufficient for a reliable conclusion, use UNCERTAINTY or BLOCK as appropriate instead of manufacturing certainty.

If a report is already correct and satisfies applicable requirements, the audit should confirm that result rather than introduce artificial changes.

## Cross-agent conflict accountability

If specialist results contain conflicting certainty claims tied to the same evidence, FINAL_AUDIT must explicitly cover each detected conflict. The audit must contain at least one finding whose `evidence_ids` include the complete evidence set of each conflict. Coverage does not mean choosing an agent by authority; the source evidence must control the conclusion.

If any conflict is not covered, the ENGINEER CORE final status is `UNCERTAINTY`. If the source evidence cannot resolve a covered conflict, the audit should remain `UNCERTAINTY` or `BLOCK` as appropriate.

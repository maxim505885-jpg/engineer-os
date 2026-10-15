# Normative rule registry contract — 2026-10-15

Added optional `engineering/normative/rule_registry.py`. No clauses, normative limits,
latest-edition assertions, official sources, or real engineering conclusions are
preloaded. This module extends existing source verification, authority review,
substantive review and decimal quantity comparison; it does not replace them.

## Contract and bounded result

A `RuleRegistry` contains up to 1000 immutable typed `Rule` records with unique
(rule_id, rule_version) pairs. Each rule declares document, edition, scope, clause,
exact requirement text, normative source SHA256, an inclusive effective-from/until
interval, operator, decimal-string limit and explicit unit. SHA256 binds all exact
rule fields. An `AssessmentReceipt` names the version and its digest, assessment
date, typed source/authority/substantive review receipts and `ActualQuantity`.

The actual quantity retains a decimal-string value, explicit unit, unique evidence
IDs, source SHA256, locator and data class. PROJECT, ACTUAL, MEASURED, TESTED and
CALCULATED remain distinct caller declarations. UNKNOWN/ASSUMED/INTERPRETED are
insufficient for this comparison-ready contract. Referenced evidence is not loaded
or independently authenticated by this module.

Source and authority records must match the rule's document, edition, source identity
and clause, and each other. A recorded VERIFIED source decision alone is insufficient:
applicability must be recorded APPLIES, actual input status DOCUMENTED, substantive
assessment date identical, and assessment date within the rule's declared interval.
Missing/stale/mismatched sources, identities, versions, inputs or dates BLOCK.
Unknown/out-of-scope applicability, unverified inputs or unresolved warning retain
UNCERTAINTY without comparison readiness. Conflicts and recorded ERROR/BLOCK stop
readiness. Invalid numeric values, unsupported units and dimension mismatch BLOCK
through existing `compare_quantity`.

A complete record yields **UNCERTAINTY, comparison_ready=true**, an arithmetic-only
comparison and deterministic receipt SHA256. The satisfied flag means decimal
arithmetic with the declared unit conversion; it does not establish the truth,
currentness, legal applicability or completeness of the normative rule or actual
input. A false comparison is not automatically an engineering ERROR. Every output
keeps acceptance_granted=false, engineering_verified=false,
normative_truth_verified=false, current_edition_verified=false. Source/reviewer
records and effective intervals are explicitly not self-authenticating. No arbitrary
PASS flag grants ENGINEERING_ACCEPTED. Review systems must not treat comparison_ready
as a normative approval credential.

## Verification

TDD RED: the new synthetic test module failed because rule_registry did not exist.
After implementation:

```
.venv-engineering/Scripts/python.exe -m unittest tests.test_normative_rule_registry tests.test_normative_verification tests.test_normative_substantive_review tests.test_normative_review_replay
```

Result: 25 tests PASS, zero failures/errors (16 new registry contract tests plus
existing normative regressions). Synthetic clauses and limits used in tests are
labelled SYNTHETIC. Coverage includes converted-unit arithmetic, false comparison,
stale/missing/invalid effective intervals, version and exact requirement digest
mismatch, unsupported units/dimensions/NaN/bool values, source edition/hash/decision
mismatch, missing review receipts, applicability/input conflicts and uncertainties,
missing/duplicate evidence IDs, authority binding, duplicate registry versions,
review dates, receipt digest sensitivity and inability of PASS review to grant approval.

## Actual-source limitation

The parent audit reports 459 candidate citation occurrences in the actual DOCX
census, with no standalone verified normative documents in the user folder. This
module has not inspected those candidate citations or authenticated any official
normative source. No web current-edition verification was performed or claimed.
Actual normative acceptance remains BLOCK. Candidate citations are discovery inputs,
not verified rule records. This implementation supplies a replayable contract for
future source-verified engineering review, not an automatic normative certification.

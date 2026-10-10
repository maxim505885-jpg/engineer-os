# Automatic LIRA upload observations — 2026-10-09

User goal: attach a calculation file/package and receive an analysis without manually copying model records. Implemented on feat/lira-upload-analysis-20261009, based on release candidate tree 2c36ea304797f56e69562d1673f3ee018d364bbe. Not installed on the user's Windows PC and not merged.

The existing original-preservation upload path now recognizes full UTF-8 LIRA TXT by document markers, calculation protocols by content, ALD metadata and COP capacity tables. ZIP packages receive per-member observations with original/member SHA256. No package extraction to filesystem or nested ZIP recursion. Limits: 100 MiB original/expanded, 64 ZIP entries, bounded central directory, no ZIP64/encryption/unsafe names/symlinks. RAR is not implemented. Binary LIR retains its existing identity-only behavior.

TXT counts and literal ordinal node/stiffness references are analyzed across the full source, independently of the 100,000-character raw preview. COP capacities remain separate from actual pile forces. ALD metadata does not prove results. An interrupted protocol explicitly reports INTERRUPTED_BY_USER. A static control step does not establish whole-run completion. No successful-run detector, model/run cryptographic binding, proprietary binary decoder, engineering acceptance or automatic LIRA control is claimed.

The upload card displays the observation report and scope; coverage/model context retain it with omitted-member disclosure for large packages. Raw source text is not replaced by derived findings, so evidence matching continues to use the original preview. Parser implementation enters analysis identity.

## Validation

- Python full suite: 784 tests, 767 passed, 17 skipped, 0 failures (66.392 s). Environment-dependent skipped checks are not claimed as executed.
- New regression tests: 14 passed, including full TXT beyond preview, broken framing, nonfinite coordinates, invalid references, interrupted/incomplete log, XML entities, invalid encoding, unsafe ZIP, persisted package and COP/ALD scopes.
- Existing document intake 7 and calculation intake 4 passed.
- JavaScript dashboard tests 7 passed; app.js syntax and git diff whitespace checks passed.
- Actual uploaded TXT models produced nodes/elements 119779/127776, 37083/44086, 83152/94775; invalid node/stiffness references and repeated node references 0 for each. These match the independent earlier source review; grammar and engineering semantics are not qualified.
- Actual section2 ALD yielded 22 rigid, 44086 element-block, 2 dynamic metadata records; COP four tables of 65 pile capacities. Capacity values matched the earlier independent review.
- Local Chromium smoke blocked: browser executable absent. Local DOM smoke blocked: jsdom absent. The browser regression was extended for TXT and log uploads/persistence; GitHub CI must run it before merge.

## Remaining

Native LIR semantics, solver/results/structure correlation, normative review and engineering acceptance remain open. Tables in CSV/XLSX use the existing unverified source path; automatic result semantics are not implemented. Point6 remains partial; global plan stays 8 ready / 8 partial / 3 open. No release or installation claim.

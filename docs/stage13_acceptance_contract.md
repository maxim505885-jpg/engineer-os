# Stage 13 — two distinct acceptance decisions

**A. Document Intelligence module readiness:** a software release decision. The module must demonstrably ingest PDF/DOCX, extract native text and source-mapped tables, preserve formulas/media, support drawing OCR without hanging or silently passing damaged regions, preserve source identity and uncertainty statuses, and pass automated integration regression. Each claim must have linked test/evidence. All nine required checks must be PASS; missing/UNCERTAINTY/BLOCK means BLOCK.

**B. Source document qualification:** an engineering evidence decision for each document. Complete source scope, cell values, vector captions, OMML formula rendering, embedded graphic rendering and provenance must each pass source-based validation. Missing or unconfirmed material remains BLOCK. This must NOT prevent software-module release when A independently passes.

`engineering.document_intelligence.stage13_acceptance.audit(module_checks,document_checks)` returns distinct `module` and `document` statuses and a strict combined `overall_status`. It is a gate, **not** a test runner or evidence factory; an input marked PASS without test evidence is not reliable. Do not auto-populate PASS from extraction counts, zero exceptions or the existence of a script.

**Current evidence (10 October 2026):** integration branch contains PR109–PR120 including source inventory, table frame filtering, bounded/adaptive vector OCR, and test fixtures. Core/Security CI PASS on the PR120 head. V4 PDF 534-page native-content inventory done; selected tables detected. DOCX V4 ZIP/XML inventories detected 41 OMML and 654 embedded media (including 138 EMF). 40 vector sheets have only partial corner OCR and sample-region recovery. None of these counts certifies source-semantic accuracy. **Module A remains pending independent full integration evidence; Document B remains BLOCK.**

## Sequence

1. Build one real-source integration fixture replay for core PDF/DOCX extraction and verify error reporting.
2. Bind tests and full source identity hashes to each module A criterion; reject unexecuted checks.
3. Issue A only after all nine criteria have evidence and CI success.
4. Treat V4 semantic qualification as separate stage B: verify tables, drawings and visual OMML/EMF across scope.
5. The user can move to the next product roadmap milestone once A passes, while B remains an explicit document review workstream. No falsified 100% extraction claim.

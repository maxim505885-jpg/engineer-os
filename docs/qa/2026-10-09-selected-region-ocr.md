# Selected region OCR — 2026-10-09

Scope: point 13, bounded recovery of small numeric labels. Not complete-document verification or accepted engineering evidence.

The original regional run read a dimension as `82406`; visual spot review showed `82400`. Whole-page OCR missed it. A selected crop `[760, 795, 950, 830]` on page 1 of source SHA256 `6092ab2298bf328a545379a850b0a740cc40f3c5592703fbf876c32f459913ce` now yields `82400` with original page coordinates. This is one assistant-reviewed spot, not qualified ground truth for the entire corpus. The older contradictory candidate is preserved.

Use `python -m scripts.local_ocr_region SOURCE --page N --bbox L T R B --sha256 EXPECTED --output NEW_JSON`. Points are unrotated and relative to the crop. Selected execution uses one pass, PSM 6 and scale up to 6, constrained by existing pixel, byte, word and deadline limits. Defaults retain whole-page/regional behavior. Output records settings, source SHA256 and boxes; flags for quality, full-page/document completeness and acceptance remain false.

The diagnostic probe initially produced empty TSV rows because this local model directory lacks Tesseract's named `tsv` configuration. Retrying with `-c tessedit_create_tsv=1` established the result; production already used this setting.

Tests were added before implementation: selected-region cases initially failed with missing API; CLI case failed with missing module. Passing checks cover cropped/rotated source coordinates, invalid selections, interrupted execution, original SHA guard, independent live numeric fixture, and refusal of existing source/symlink/hardlink output aliases. Review found inaccurate selected engine settings; these are now recorded explicitly in identity and per-pass dossier.

Pre-final suite: 745 tests, 743 passed, 2 native Windows-only skips. Additional live-numeric and CLI-alias tests passed; final complete suite and remote CI must be recorded separately before integration.

Real selected pass: 239400 pixels, 354 output bytes, 3 words, 1/1 completed pass. The source hash remained unchanged. The source still emits MuPDF xref warnings. Tables, formulas, merged cells, all drawing labels and full corpus completeness remain unverified. Project readiness stays 8 done / 8 partial / 3 open.

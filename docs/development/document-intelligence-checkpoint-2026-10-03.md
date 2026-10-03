# Document Intelligence checkpoint — 2026-10-03

## Confirmed work

The original V4 source is 74,522,583 bytes, 534 pages, SHA256
`b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`.
All pages received a native PDF structural inventory: 40 have no native text,
193 have fewer than 250 native characters (including those 40). These counts
identify review/OCR needs; they do not prove document extraction completeness.

The full column-comparison table on pages 396–404 was investigated separately
using original PDF line geometry and native text. The experiment preserves
101 physical grid rows, 606 grid cells and assigns all 1,015 in-region words.
Two header rows and four spanning section rows are tracked separately. Four
split body rows were manually reviewed at 397–398, 398–399, 401–402, 402–403.
Each six-cell candidate retains both source fragments with page/bbox/hash
provenance, including empty cells. This yields 91 logical body-row candidates.
28 conflicting-input probes block and four non-split boundaries do not join.
Column alignment, original text and row sections were checked; this is not a
generic table parser or independent engineering validation of all 91 rows.

The source values, units, commas, slash notation and line-break hyphens remain
literal. No arithmetic, normative or capacity conclusions were derived.
The table header's repeated numeric label `5` was preserved as source content,
not silently renumbered. Named columns come from the reviewed source header.

The current code's false-header guard and cache check version 6 are published
in draft PR #27 (`fix/docling-continuation-region-audit`), stacked on draft #26.
142 Python tests, Python compilation and JavaScript syntax checks passed.
Code commit `aff3bd3869bdb43e4c912f4e8b7ae73e519b6237` has successful CI run
37149715279. PR #19 remains open/draft at `da4c9fd7ea7716c22720a50b635e47e20b95b8b9`.
Neither main nor any merge was changed.

## Remaining blockers

- Production Docling does not recover reviewed cross-page/header mappings.
  The new page 404 local log reports missing/ambiguous column-header metadata.
  No successful fresh 396–404 batch is claimed.
- Runtime approval review twice rejected result polling for a possible
  Microsoft telemetry connection with unknown payload, including an attempt
  with ONNX telemetry disabled and Python network restrictions. Further Docling
  launches were halted; the local log does not establish what any payload was.
- Historical full-document extraction still needs rechecking under version 6.
  The prior 137 blocked pages and review queue are historical, not fresh counts.
- Visual/semantic review, OCR coverage on graphics/scans, normative and
  engineering validation, and FINAL AUDIT remain unfinished.
- The user's Windows environment was not accessed; Linux results do not
  establish the Windows Docling/Ollama installation state.

All recovery artifacts remain UNCERTAINTY / NOT_EVIDENCE. Whole-document status
is BLOCK; no ACCEPTED, Evidence Register writes, Supabase writes or FINAL AUDIT.
The private stage archive includes reproduction scripts, original-source
previews, cell-level provenance, negative probes, the native 534-page inventory,
runtime log and explicitly historical backlog.

Next implementation should consume explicit reviewed continuation mappings,
verify all six cells and source coordinates, preserve empty/multifragment cells
and section boundaries, and keep candidates untrusted. Before full OCR reruns,
resolve the runtime safety restriction with established network/telemetry scope.

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

The earlier false-header guard and cache check version 6 were published
in draft PR #27 (`fix/docling-continuation-region-audit`), stacked on draft #26.
142 Python tests, Python compilation and JavaScript syntax checks passed.
Code commit `aff3bd3869bdb43e4c912f4e8b7ae73e519b6237` has successful CI run
37149715279. PR #19 remains open/draft at `da4c9fd7ea7716c22720a50b635e47e20b95b8b9`.
Neither main nor any merge was changed.

## Fresh controlled checks after user authorization

The user authorized resuming runs despite the possible telemetry risk. ONNX
telemetry remained disabled, HF was offline and Python socket connections were
restricted. No claim is made about the payload or origin of the earlier alert.

Under check version 6, the nine isolated pages 396–404 all BLOCK (201.65 seconds
total, maximum cumulative child peak RSS 1,883.66 MiB). The causes are merged
cells, missing grid cells, mixed stamp/body content and ambiguous header flags.
Seven controls were also run: pages 1, 12, 15, 16, 499 returned UNCERTAINTY;
11 and 500 BLOCK. Page 500 required 88.076 seconds and failed on ambiguous cells.
These version-6 reports remain labelled version 6, not current cache entries.

Page 11's failure was diagnosed as a bottom 3×7 stamp whose label was exported
as `Кол.уч Лист`. The filter now recognizes this exact combined label while
retaining dimensions, bottom-position bounds, cell count and whitelist checks.
Engineering content inside that candidate stamp still prevents exclusion.
Check version 7 invalidates older caches. Independent code review found no
critical or important defects; all 144 Python tests passed.

Fresh version-7 runs succeeded with UNCERTAINTY on page 11 (26.146 seconds) and
the original pair 15–16 (24.962 seconds). All seven reviewed table rows on page
15 and the checked section heading on page 16 match the declared baseline.
This closes that bounded table regression, not completeness of both pages.

Page 499 retains 213 blocks but OCR reads `ФС3` as `ФСЗ` and `ФС6` as `ФСб`.
Only nine of eleven reviewed diagram identifiers match; the identifier
comparison is ERROR. These values were not silently corrected or registered.
Page-level conversion success therefore cannot imply diagram verification.

The 91 native table candidates now retain section/header links, deterministic
IDs and 570 original body-cell fragments. A dry check of four cross-page rows
preserved both source pages through the existing document/evidence contracts;
the contracts validate provenance only and no persistence was called.

## Remaining blockers

- Production Docling does not recover reviewed cross-page/header mappings.
  Page 404 reports missing/ambiguous column-header metadata; the fresh nine-page
  batch remains BLOCK. The experimental native recovery is not installed as a
  production fallback.
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
and section boundaries, and keep candidates untrusted. Future controlled OCR runs retain the disclosed offline and telemetry safeguards;
full-document reruns remain inappropriate until structural recovery is validated.

# Current-corpus continuation: document qualification, 2026-10-16

## Continuation checkpoint — 2026-10-17

The source-preservation script was rerun: all 52 registered files remain
unchanged, with no added or missing files. A private, diagnostic-only derivative
now combines the two previously isolated image/layout controls, the three
source-traced PAGE fields, and exact source PNG payloads on pages 7–9. Its bounded
source-object gate reports 3/3 assignment rasters matched, with footer labels 4/5/6.
The PDF remains 68 pages; full-page comparison shows changes only inside the three
target image areas for the exact-raster insertion. Frame text/orientation and page
layout still differ from the native capture. This derivative is not a production
fix or a full-report qualification, and the original v4 PDF still lacks the second
assignment sheet.

The imported logical-cell review found 521 exact text matches, 30 cells requiring
visual review, one missing cell and one mismatch (a page-break marker). The 30
complex cells were inspected in 13 native/derived page-pair sheets: visible text
matches after removing nonprinting control characters; 28 raster assets and one
WMF were visually located in the corresponding table regions. All 28 raster assets
were found among actually drawn PDF images; two map one derived page earlier after
text reflow. The snow-load table and the critical diagram received additional
large-scale visual comparison. This does not qualify every table boundary, image
scale/crop, formula, or numeric value across the report.

A separately scoped native-PDF versus derived-PDF comparison on reference page 2
covered 116 table-cell records. All 68 cells marked as critical numeric matched;
113 records matched overall and three remain unresolved (two symbol-only cells and
one reordered Greek-letter expression). No mismatch in the marked numeric cells
was observed in this page-level check. It does not extend to other pages or
establish engineering correctness.

Accordingly, T03/T04 remain BLOCK and the report remains DERIVED_UNVERIFIED.
The assignment-raster omission is resolved only in this private diagnostic
candidate; document layout, all-page tables/numbers, and complete source-view
fidelity are still unqualified. No acceptance or FINAL_AUDIT is granted.

Status: T03/T04 remain BLOCK for faithful Office source view. This is a negative
qualification result, not engineering acceptance or a release audit. The tested
baseline is `cac54476b84de4bb3a6f86fc7562f5bd56a768eb` on
`codex/v1-completion-20261015`. GitHub REST confirmed PR #155 open and draft with
that exact head before changes. Main checkout was not modified.

## Evidence boundary

Only the controlling user-supplied folder was used for engineering evidence.
Its current register contains 52 files; a fresh read confirmed all 52 hashes
unchanged, no added files and no missing files. Private filenames, source hashes,
images, locators and receipts remain under the ignored `.engineer-os/tzz-stage2`.
No source documents or private hash register accompany this QA note.

The older readiness audit describes a different source set. The current folder
contains five DWG files with five distinct identities, three SPR files (including
copies), and no LIR, IFC or DXF files. Therefore the historical two-DWG/geodesy/
nine-LIR results cannot qualify this current source set. SPR/SAV/SEC files and
SCAD companion files are present; their presence does not establish a qualified
SCAD adapter, result extraction or solver execution. Historical task requirements
remain in scope, but unavailable historical sources cannot be silently substituted.

## Page correspondence and actual negative result

The supplied reference PDF has 65 pages; the guest-derived PDF has 68. Full-document
token alignment and visual overview of all pages were performed using 17 paired
sheets. Ambiguous pages dominated by scanned images were resolved by visual review;
text matching alone is not a reliable mapping for those pages.

- The first two reference title pages become derived pages 1–2 and 3–4. In each
  case the city/year line is moved onto its own page. These account for two added
  pages; they are not wholly empty pages.
- The main text is reflowed across derived pages 15–20 relative to reference
  pages 13–17. The following section starts at reference page 18 / derived page 21,
  and the end is reference page 65 / derived page 68. This accounts for the third
  added page. Several formulas and a figure also move between later paired pages.
- The second scanned page of the technical assignment is visible on reference
  page 6 but absent from derived page 8, which contains only frame/footer content.
  Passive inspection of the native DOC found its PNG in an OLE stream. Its decoded
  RGB pixels match the reference image exactly, including dimensions. The derived
  page has zero image objects; no image with those dimensions was found in the
  derivative image objects. The missing visible content is confirmed independently
  of the page-count difference. The cause inside the renderer remains UNKNOWN.
- Overview also found changed frame geometry, corrupted vertical frame text and
  repeated/overflowing footer numbering. These prevent layout-equivalence approval.
  One certificate has a visible color difference; attribution to renderer versus
  source/reference revision remains UNKNOWN.

The existing `qualify_document` gate was exercised with a source-bound manifest
for the single confirmed missing raster and no matching observation. It returned
BLOCK, named the missing object, and retained `acceptance_granted=false`.
This deliberately limited manifest is not a complete census of the document.
The private `page-correspondence-v4/qualification-block.json` binds the negative
result to the source, reference, diagnostic script and derived PDF identities.

The 17 overview sheets establish page/layout review coverage. They do not establish
all-cell/all-number/all-formula fidelity. Selected formula pages were inspected at
larger scale; several preserved expressions moved to adjacent pages. No solver or
normative correctness claim follows from that inspection. All critical object
comparison and native layout qualification remain incomplete.

## Current five-DWG probe

All five registered current DWGs were hash-checked and copied into new private
staging directories. Installed ODA 27.1.0 was copied to a separate private runtime;
all 56 runtime files were hashed before and after, with no content changes.
Each process ran in the existing Windows AppContainer primitive with zero
capabilities, a Job with 2 GiB per-process / 3 GiB total memory and four-process
limits, a 60-second timeout and a 64 MiB monitored output budget. The installed
runtime was not modified. The helper returned normally after owned cleanup.

All five converter processes exited 0 in 2.965–3.288 seconds, but every derivative
is structurally incomplete. Streamed group-pair inspection found HEADER, CLASSES,
TABLES and BLOCKS; only three ENDSEC records and no EOF record. All stop at the
same INSERT handle inside BLOCKS before any ENTITIES section. This is evidence of
an incomplete export, not proof that the original DWG is corrupt. The output
sizes are approximately 24.5–26.7 MiB and exceed the existing application budget.
Actual `run_cad(CAD_INVENTORY)` calls rejected all five with CAD_SOURCE_SIZE_LIMIT.
The original and staged DWG hashes remained unchanged in every probe.

A separate repeat of the first source instrumented the existing termination
boundary: the owned Job had zero active processes before both cleanup calls.
This rules out a still-running owned descendant being killed by those cleanup
calls in that repeat; it does not identify the converter's internal failure.
The same incomplete endpoint reproduced. No repair, native save or budget
increase was attempted. No source census, geometry fidelity or roundtrip PASS is
claimed. Current qualification remains BLOCK for all five DWGs.

A separate control changed only ODA's audit flag from 0 to 1, retaining the
ACAD2018/DXF target and the same zero-capability AppContainer, time, memory and
output limits. All five processes exited 0. Section-level scans found `ENTITIES`
and `EOF` in every output, with `OBJECTS` and either `ACDSDATA` or
`THUMBNAILIMAGE` afterward; the repeated first-source run returned the same byte
size and section markers. Outputs ranged from 30,241,793 to 62,979,017 bytes,
each above the application's 20 MiB CAD intake limit. The originals, staged DWGs
and copied ODA runtime remained unchanged. These derivatives were not accepted by
the application parser, and no entity, geometry, layer, unit or roundtrip
comparison was performed. Audit mode avoids the prior `BLOCKS`-only endpoint in
this bounded probe, but it is not a qualified fix; source fidelity and normal
application use remain BLOCK.

Private receipts are in the current-corpus CAD probe directory under
`.engineer-os/tzz-stage2/`; the structural diagnostic and actual application-gate
results are preserved separately from the conversion-process receipt.

## Consequences and next work

The v4 transport successfully delivered bytes, but the resulting PDF fails faithful
source-view qualification for this actual document. Retain DERIVED_UNVERIFIED and
BLOCK qualification; do not promote the renderer or substitute its blank assignment
page as evidence. The supplied PDF/native source remain available independently.
No production configuration, source files, review authority or acceptance gates
were changed. The root cause of the omitted raster needs a controlled native-image
reproducer before any renderer fix can be claimed.

T06–T09/V01 must use the current register. The five current DWG probes establish
incomplete exports; loss and roundtrip qualification remain blocked. There
is no current-source geodesy DXF or LIR to rerun. Real IFC qualification is blocked
by missing input. Current SPR/SAV/SEC/RTF/XLSX can be investigated without asserting
LIRA/SCAD support or running a solver. T10/T11 real acceptance and FINAL export,
T12 physical Windows/offline/second-machine checks and T13 release remain open.
Do not merge, tag or release automatically.

## Verification

Fresh existing CAD conversion/roundtrip/local-app regression: 17 tests OK.
Fresh Office/document/transport regression: 56 tests OK in 7.282 seconds.
These are implementation checks, not document equivalence or object acceptance.

A private binary-DXF size control used the smallest audit=1 derivative (30,241,793
bytes) and ezdxf 1.4.4. The converter wrote a 391,907-byte binary candidate, but
read-back in the same zero-capability AppContainer exited 1 with
`DXFStructureError: missing ENDSEC tag`. This candidate is unusable for intake;
its smaller size is not evidence of preserved content. No application ingestion,
entity-fidelity comparison, or conversion acceptance was performed. Binary DXF
is rejected as a size workaround for this corpus unless a separately validated
writer/read-back path is established.

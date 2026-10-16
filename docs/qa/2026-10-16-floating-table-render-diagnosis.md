# Controlled Office context diagnosis — 2026-10-16

Status: TESTED diagnostic recovery of three assignment rasters; T03/T04 remain
BLOCK for full source/layout/graphics qualification. No production renderer or
bundle configuration changed. All source payloads and receipts remain private.

## Reproduction and controlled reductions

The same imported package, image payloads and XML namespaces were retained.
Only declared body/section changes were made in separate private derivatives.

| Control | Pages | Assignment rasters drawn |
|---|---:|---:|
| Two original image paragraphs and final section | 3 | 3 |
| Same paragraphs and original image-containing section | 3 | 3 |
| Original body prefix through the third image and active section | 9 | 2; third absent |
| Same prefix minus the intervening empty table | 9 | 3 |
| Minimal active-section control plus that empty table | 3 | 2; third absent |
| Full imported document minus only that table's floating-position property | 68 | 2; second absent |
| Full imported document with second image in separate paragraph, floating table retained | 68 | 2; third absent |
| Full imported document combining paragraph split and floating-position removal | 68 | 3, on pages 7–9 |

The empty table has two cells and no payload text. Its presence is sufficient to
reproduce loss of the third raster in the reduced control. Whole-document results
also depend on the shared image paragraph and surrounding layout; removal of one
property alone does not fix the full document. Do not generalize this into a rule
that all floating tables may be removed or normalized safely.

For the combined derivative, reversing the two declared XML changes gives canonical
XML identical to the imported document. Every other ZIP part is byte-identical.
All three restored assignment sheets were inspected against the same-source
native Word/GDI pages. The original DOC was never modified. This establishes the
specific visual recovery, not original layout or engineering equivalence.

## Remaining import/export boundaries

Native reference footers on the three pages read 4/5/6; the combined derivative
still shows 17/17/17 and misoriented frame text. Its imported header contains literal
numbers and no field instruction or simple field. Passive binary-source scanning
finds PAGE tokens, but does not establish their exact header/story assignment.
No source field reconstruction or complete binary-field parse is claimed.

A further explicit PAGE-field rendering control replaced the two literal header
numbers with PAGE fields in a separate derivative. The resulting lower-right
numbers on pages 7/8/9 are 4/5/6, matching the native references; page 8 was visually
checked. This demonstrates that the renderer can evaluate a field once supplied,
whereas the imported header already contains literals. It does not establish an
automatic, source-faithful field reconstruction rule. The original and production
configuration remain unchanged; frame/text orientation is still incorrect.

The original v4 PDF encodes the surviving first/third PNG assignment sheets as
JPEG. Same-size decoded RGB comparisons measure nonzero differences. The second
sheet is absent from drawn-image observations. Resource dictionaries are not
used as page-presence proof: the private raster census was recalculated with
actual drawn-image xrefs; its totals remain 29 exact RGB matches, 51 requiring
review and two WMF parts excluded. Nonmatches do not by themselves prove loss.

## Bounded source-field provenance and text-flow control

A passive, bounded parse of the source binary now follows the three relevant
numeric PAGE fields through their field PLCs, textbox records, OfficeArt shape
IDs and header anchors to the three imported section-header parts. Their cached
values correspond to the native page labels 4/5/6, and each imported header part
contains the matching numeric text twice (choice and fallback). This resolves
the earlier uncertainty for these three fields only. It is not a general DOC
parser or a complete format/layout qualification. The parse followed the public
MS-DOC definitions for [field PLCs](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/751b09bb-72f0-45ef-8e87-666dea68219f),
[header textbox mappings](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/efaa9508-5dcb-4bcb-8468-87939ea34181),
and [OfficeArt text-flow properties](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-odraw/8234eb61-3963-40ee-a025-a80cc7c4f628).

A separate minimal rendering control translated the three source bottom-to-top
text labels from rotated wide boxes into narrow boxes with vertical text flow,
preserving each axis-aligned box boundary. LibreOffice stacked the characters
vertically and did not reproduce the readable native labels. This is a negative
control, not a candidate repair. The full-report frame rotation problem remains
open; no generic rotation or vertical-text rewrite is qualified.

The combined derivative is explicitly unverified. Remaining work includes native
page correspondence, all complex cells/critical numeric content, frame geometry,
numbering and image/vector fidelity. No automatic normalization, renderer
promotion, engineering acceptance or FINAL_AUDIT follows.

## Verification and CI

All 52 registered sources remain unchanged, without additions/missing files.
The current published code/docs commit `9619941de662cc390790bf4313e6cdeba7bfcdda`
passed Core, Optional adapters, Security and Windows workflows. Windows attempt 1
failed while starting PowerShell with 0xC0000142 before pip-step output, and artifact/
post-job executables also failed. A scoped rerun of the same unchanged job passed
(attempt 2, job 116944543626, run 38891981986). No workflow relaxation or product
change was made. That successful retry does not prove a cause for the first host
failure. New documentation commits require their own CI observation.

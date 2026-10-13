# Word reference and Windows document CLI verification

Base: integration/release-candidate-v1 b2c29604d3a8a2a8079a670a7affca4f55b2b9c6, tree c1f44ad1839ecf763faedb98deaf87fd219e5e75. Task13 remains OPEN. Authority: maintained master-plan B2/B3 and codex-handoff-20261013.md on docs/project-map-handoff-20261005.

## Verified on 2026-10-13

- V4 DOCX: 147,560,922 bytes, SHA-256 `c0ca593f4dec5c101d01282523032e05b147e9169fb043a144af5fbd479a5685`; 694 ZIP entries with CRC pass. V4 PDF: 74,522,583 bytes, SHA-256 `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`. The source DOCX and byte-identical working copy hashes stayed unchanged.
- Installed Microsoft Word 2021 build `16.0.14228.20204` produced 491 pages. After explicitly updating 57 PAGEREF, 11 SEQ, and one TOC field, plus the shared PAGE field in two section placements, the before/after exported PDFs had identical native text and raster hashes on all 491 pages. Hyperlink and embedded-object fields were not activated or updated.
- Against the first 491 pages of V4 PDF, 483 pages had exact extracted text, 489 had equal text after whitespace removal, and all 491 page dimensions differed by 0.12 pt in each axis. Pixel hashes did not match on any page. The two text-multiset differences are TOC dotted-leader counts; other native-text differences are whitespace. This supports bounded text correspondence, not visual equivalence.
- V4 PDF has 534 pages. Pages 492–534 are the 43-sheet graphic appendix; the Word export ends after the drawing index on page 491. The DOCX reader reports 21 embedded OLE objects (about 45 MB) as unread, 696 image references, 41 equation units, and 11 `unsupported_body` units. The 11 units were confirmed to be empty `bookmarkEnd` markers. The graphical appendix has almost no native text; page-vector content remains unverified and local Russian/English OCR models are unavailable. These are unresolved completeness criteria, not ACCEPTED content.
- Full Windows suite after the CLI fix and deterministic ZIP fixture correction: 1,058 tests, 0 assertion failures, 13 errors, 49 skips. Remaining errors are Windows symlink privilege failures, temporary-file locking, and SQLite cleanup locks; skips include unavailable OCR models, platform-specific Linux security checks, and optional table OCR dependencies. Full raw log SHA-256: `a4c805e12aaf4ca9a97deeacc602e5b7f2eaeaca0ce600eb30d9bcc00b317aa8e` (private local QA).
- A real subprocess test reproduced Cyrillic JSON output failing under ASCII stdout. JSON stdout now escapes non-ASCII; UTF-8 report files and status gates are unchanged. The regression test passes under ASCII stdout. The stage7 test ZIP fixtures now use fixed timestamps so repeated snapshots compare deterministically.

## Remaining work

1. Resolve whether the 43 PDF drawing sheets correspond to embedded DOCX objects or are appended only in the PDF, then read the complete graphical content with local OCR and visual source-bound checks. Do not infer labels from the drawing index.
2. Qualify OLE/WDP/EMF object placement, all page-level graphics, fonts and physical layout against the original. Word was diagnostic only; it is not a new runtime dependency.
3. Run the exact-head GitHub workflows and review the proposed candidate PR. Keep item 13 OPEN until the unverified graphic/object content and the remaining source-bound criteria are resolved.
4. Update the maintained map, master plan and handoff with the candidate commit/PR and exact CI results. No engineering acceptance or LIRA/SCAD calculation is in scope.

QA scripts/exports/raw document text remain private local evidence. Word is an existing diagnostic reference; no mandatory Word dependency, paid API or installed commercial fonts are introduced. Calculations remain deferred. Absent symlink privileges/OCR languages/renderers must be reported, not bypassed to mark complete.

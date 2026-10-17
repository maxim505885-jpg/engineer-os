# Windows engineering profile

`scripts/prepare_engineering_profile.ps1` probes the existing isolated
`.venv-engineering/Scripts/python.exe`; `-Python` selects another explicit
interpreter. `-InventoryOnly` performs no subprocess functional probes. The
command never installs packages, downloads models, replaces the base environment,
or modifies the running application. Repeating it replaces only the diagnostic
`.engineer-os/profiles/engineering/capability-report.json`.

`requirements-engineering-windows.lock` records the exact installed package
versions observed on Windows CPython 3.13 x64. It is an environment snapshot,
not a verified redistributable wheelhouse or a hash-locked installation bundle.
It includes inherited packages; it does not assert that all are required.

Inventory exposes `installed`, `configured`, `probe_status`, `ready`, version,
available executable/model hashes and limitations. Installed is never READY.
Probes run only on fixed synthetic inputs, in separate timeout-limited children:
PDF text/raster, Russian/English image OCR with boxes, a declared IFC fixture,
and the supported UDL beam compared with closed-form reactions/deflection.
The reported READY applies solely to that named synthetic probe, not general
corpus coverage. An unavailable fixture, dependency or output blocks its probe.
Optional failures do not prevent base chat from starting.

Tesseract discovery honors an explicit `ENGINEER_OS_TESSERACT_BIN` first; an
invalid override fails closed. Otherwise PATH and standard Windows ProgramFiles
locations are checked. Both local rus/eng traineddata files remain required.
The OCR adapter and inventory use the same discovery function.

The diagnostic JSON is unsigned, has no verification authority, is not consumed
by FINAL_AUDIT, and is not a portable cache of capability readiness. Its build,
tool and model identifiers describe the observation; editing it grants no trust.
HF offline settings prevent downloads in the fixed probes but are not a Windows
network sandbox. Native extension memory isolation is not yet qualified.

On 2026-10-15 the actual Windows probes passed PDF/OCR/IFC/beam. Tables remained
BLOCK because the offline model profile was not qualified. Office remained BLOCK
because Windows source-render isolation was not qualified. Existing Microsoft
Word does not by itself meet that isolation requirement. No LibreOffice binary
was found in standard ProgramFiles locations or registered application paths;
that is not an exhaustive disk-wide absence claim. T02 remains open until
offline models, wheel/model provenance, Office isolation and reproducible
preparation are qualified.

The full native test pass with the installed fast models exposed one genuine
unresolved glyph mismatch in the real printed-label corpus (`Прогиб20мм` became
`Прогид20мм`). Parent-to-child executable propagation and UTF-8 fixture decoding
were corrected separately; the recognition assertion remains unchanged. Official
`tessdata_best` rus/eng models at revision
`e12c65a915945e4c28e237a9b52bc4a8f39a0cec` were evaluated in a separate profile and
rejected: five fixture mismatches, including Latin reinforcement notation. They
were not promoted or installed over system models. Their private provenance
receipt retains the upstream URLs, SHA-256, byte counts and Apache-2.0 license.
The model source is the official [Tesseract repository](https://github.com/tesseract-ocr/tessdata_best).
This reinforces the distinction between passing a simple OCR probe and qualifying
the real engineering corpus.

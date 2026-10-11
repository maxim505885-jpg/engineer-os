# Offline raster table candidate adapter

`engineering.local_app.table_readback.read_tables(pdf_bytes, page, bbox, backend)`
returns JSON-compatible source-bound candidates. `page` is 1-based and `bbox` is
`[left, top, right, bottom]` in unrotated CropBox-relative PDF points. Backends are
`img2table` and `paddleocr`. Original bytes are hashed, never rewritten. The exact
selected PDF clip is rasterized once and those PNG bytes are the backend input;
no native PDF table or surrounding-page text is substituted.

The Tesseract adapter receives these exact PNG bytes on stdin and explicitly
sets `tessedit_create_hocr=1`; it does not depend on `configs/hocr` and does not
use upstream's JPEG reencoding. Geometry is detected independently of OCR and
preserved even when upstream discards empty rows/tables. Text is associated only
by identical cell bounding boxes. `TEXT_UNAVAILABLE` is explicit; no missing
text is invented. `ocr_input_png_sha256` records the actual OCR input identity.
This resolves missing-config table disappearance, not recognition accuracy:
real V4 p55 rus+eng still confuses italic `d20` with `420`. Such OCR candidates
must not be accepted without source review.

Install the optional environment separately from the core application:

```sh
python -m venv .venv-tables
.venv-tables/bin/python -m pip install -r requirements-table-img2table.txt
export ENGINEER_OS_TABLE_PYTHON="$PWD/.venv-tables/bin/python"
export ENGINEER_OS_TABLE_LANG=eng
```

On Windows use the absolute `.venv-tables\Scripts\python.exe` path. Tesseract must
be locally installed and on PATH, with all requested `eng+rus` trained languages
already installed. The adapter does not install language data. `img2table==1.4.2`
is enforced at execution. Dependencies in the requirements file are the tested
CPU set; no GPU/runtime downloader is required. Recognition is limited to ruled
tables (`borderless_tables=False`, implicit row/column inference disabled).

For Paddle install `requirements-table-paddleocr.txt` in another isolated
interpreter and set `ENGINEER_OS_PADDLE_MODELS_MANIFEST` to a local JSON file. It
must contain exactly these keys, each mapped to an absolute existing local model
directory with `inference.pdiparams` and `inference.json` or `inference.pdmodel`:

```json
{
  "layout_detection_model_dir": "/models/layout",
  "text_detection_model_dir": "/models/text-detection",
  "text_recognition_model_dir": "/models/text-recognition",
  "table_classification_model_dir": "/models/table-classifier",
  "wired_table_structure_recognition_model_dir": "/models/wired-structure",
  "wireless_table_structure_recognition_model_dir": "/models/wireless-structure",
  "wired_table_cells_detection_model_dir": "/models/wired-cells",
  "wireless_table_cells_detection_model_dir": "/models/wireless-cells"
}
```

PaddleOCR 3.2.0 is enforced. PPStructureV3 receives every local model directory;
orientation, document unwarping, formula, chart and seal models are disabled.
Missing models return `UNAVAILABLE`; there is no automatic weight provisioning.
The requested language is recorded; Paddle recognition-model language is explicitly
unverified. Paddle cell geometry is separate from returned structure HTML;
cell text/spans/confidence stay null when the pipeline provides no reliable
cell-to-structure association. Table extent is the envelope of supplied cell
geometry. Paddle execution with actual local weights has not been qualified here.

Every successful or unavailable validated result includes source SHA256, selected
page/bbox, page CropBox/rotation, raster dimensions/scale/pixel origin, RGB pixel
SHA256 and PNG SHA256, language and process/network isolation dossier. Geometry
maps by `(raster_pixel + pixel_origin) / scale`; returned source geometry is
clipped to the exact selection and the before-clip coordinates are retained.
Raster pixel rounding can include a fraction of a PDF point at a boundary.

img2table merged spans come from repeated identical cell geometry, with the basis
recorded explicitly. Omitted confidence is null. Table/cell outputs are candidates:
`UNCERTAINTY`, `quality_verified=false`, `acceptance_granted=false`. Zero detected
tables is an empty candidate result, never proof that the source has no table.
No engineering or table acceptance is granted.

Missing environment/dependencies/models/language returns `UNAVAILABLE` plus a
stable reason. Invalid arguments raise `ValueError`; invalid source/page/selection
in the worker returns `ERROR`. Deadline/output/protocol failure raises stable
`TABLE_TIMEOUT`, `TABLE_OUTPUT_LIMIT`, or `TABLE_WORKER_FAILED`. Successful JSON
is bounded to 4 MiB; source to 128 MiB, document to 5000 pages, raster to 9 million
pixels, tables to 100 and cells to 10000. The 90-second wall deadline and monitored
stdout/stderr are enforced in the parent, with process-group termination on POSIX
and `taskkill /T /F` on Windows, including cleanup after normal worker completion.
The worker is invoked as `python -m engineering.local_app.table_worker` to avoid
shadowing installed modules with the local `coverage.py` file.

Linux additionally applies the existing seccomp network deny sandbox before
loading backends, CPU/address-space/file/descriptor limits, and a 4 MiB per-file
output limit. Windows/non-Linux records `network_denied=false` and
`network_isolation=NOT_ENFORCED`; there is no claim of seccomp or OS memory limits
there. Windows descendant cleanup is implemented but has not been executed here.
Backend models remain explicitly local and provisioned in advance on every platform.

## Executed verification, 11 October 2026

Linux/Python 3.12: `ENGINEER_OS_TABLE_PYTHON=/workspace/scratch/0a9c93c51c71/table-adapter-venv/bin/python python -m unittest discover -s tests -p test_table_readback.py -v`
passed 11 tests in 3.842 seconds, including genuine local img2table/Tesseract,
merged-cell geometry, exact selected-clip provenance, no-model availability,
invalid selection despite absent backend, network denial, parent timeout and
noisy stderr bounds. Synthetic ruled table returned 1 table/12 cells; merged
header fixture returned 11 unique cells with a two-column header span. An earlier
small short-text fixture yielded zero detected tables, illustrating detection
limits. Source review remains required even when the fixture is recognized.

Genuine V4 source SHA256
`b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`:
page 5, bbox `[80,60,550,720]`, img2table 1.4.2/Tesseract English-only returned
1 candidate table/5 cells in 6.703 seconds. Raster 1880×2640 at scale 4;
RGB pixel SHA256 `ed3656c85f18bd6e861f793b4f882297285ec55de676297565da62d4e0354820`;
PNG SHA256 `b3d27eda39a137a4d12588f02b00c51ceaeb039c8c0eece31a20c4dbd6444d9f`.
Only `eng` and `osd` trained data were installed; Cyrillic recognition is not
qualified and neither table correctness nor engineering acceptance is asserted.
This verifies one selected region, not completeness across the 534-page source.
Paddle real weights, Windows execution and Windows process-tree cleanup remain
unverified. Windows `taskkill` cleanup after the main process has already exited
cannot guarantee discovery of orphaned descendants; Linux process-group cleanup
does not have this limitation.

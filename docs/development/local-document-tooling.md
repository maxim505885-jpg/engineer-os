# Local document and calculation tooling

These components extend the existing application. Originals remain read-only;
derived text, tables, formulas and images are unverified candidates.

| Component | Runtime integration | Qualification boundary |
| --- | --- | --- |
| LibreOffice | Selected source OMML formula -> passive DOCX scaffold -> PDF -> PNG; authenticated formula-preview route and UI | Source fonts, full Word layout, physical pages, fields and mathematics not verified |
| Word layers/EMF+ | Exact nearest-ancestor cached bitmap, ordered declared effects and framed EMF+ record inventory in existing reader | Effects and graphics state are not applied; no full EMF renderer |
| img2table 1.4.2 + Tesseract | Optional isolated local PDF-region raster table backend and UI | OCR, cell spans and engineering meaning remain unverified |
| PaddleOCR PPStructureV3 | Optional adapter requiring explicit complete local model manifest | Missing models return UNAVAILABLE; actual model execution not qualified |
| PDF.js 5.4.624 | Vendored source PDF viewer, pages/zoom, bounded sequential canvas | No automatic graphic/table acceptance; first/last V4 pages tested |
| LIRA R4 result ZIP | Strict result reader dispatched before native input/generic ZIP readers | No real RES export, solver completion or model/result association verified |
| pywebview | Optional native window reusing Store/Worker/server/data lock | Physical user-PC window not verified |
| PyVista | Separate optional requirements for future visualization | No new native model/result viewer implemented |
| ezdxf/LibreDWG, Docling, Playwright | Existing integration retained | Existing limits and installed dependency requirements still apply |
| SCAD Office SDK | Capability inventory reports configured SDK separately from execution | Native adapter not implemented without installed version headers/DLL qualification |

## Configuration

Core install remains `python -m pip install -r requirements-local-app.txt`.
LibreOffice must be installed locally; optional `ENGINEER_OS_DOC_CONVERTER` is an
absolute path to its executable. The formula renderer opens a sanitized
single-formula derivative, never the uploaded package. Linux denies network in
the existing sandbox. Windows uses a passive scaffold and disabled links/macros;
it explicitly reports that OS network denial is not enforced.

For img2table use a separate Python 3.12 environment:

```powershell
py -3.12 -m venv .venv-tables
.\.venv-tables\Scripts\python.exe -m pip install -r requirements-table-img2table.txt
$env:ENGINEER_OS_TABLE_PYTHON = (Resolve-Path .\.venv-tables\Scripts\python.exe).Path
```

On Linux use the equivalent `python3.12 -m venv .venv-tables`, install the same
requirements and set `ENGINEER_OS_TABLE_PYTHON` to its absolute Python path.
Install local Tesseract with `rus` and `eng` language files, then set
`ENGINEER_OS_TABLE_LANG=rus+eng`. If a requested language is unavailable, the
adapter reports UNAVAILABLE. No paid service or runtime model download is needed.

Paddle is a separate optional environment from `requirements-table-paddleocr.txt`.
`ENGINEER_OS_PADDLE_MODELS_MANIFEST` points to a local JSON object with absolute
existing directories for these keys:

```json
{
  "layout_detection_model_dir": "C:/models/layout",
  "text_detection_model_dir": "C:/models/text-det",
  "text_recognition_model_dir": "C:/models/text-rec",
  "table_classification_model_dir": "C:/models/table-class",
  "wired_table_structure_recognition_model_dir": "C:/models/wired-structure",
  "wireless_table_structure_recognition_model_dir": "C:/models/wireless-structure",
  "wired_table_cells_detection_model_dir": "C:/models/wired-cells",
  "wireless_table_cells_detection_model_dir": "C:/models/wireless-cells"
}
```

Local weight/config files are required before pipeline creation. Linux network
denial and offline flags prevent fallback downloads. Model licenses must be
checked separately from repository code licenses. This integration does not
claim a successful Paddle inference without configured models.

`GET /api/tooling` requires the app token and reports installed/configured
capabilities. Package presence is not execution proof. Selected source tools
also require project/file identity and expected SHA256:

- `POST /api/sessions/{sid}/files/{fid}/formula-preview`: part, zero-based ordinal, candidate_id, expected_sha256.
- `POST /api/sessions/{sid}/files/{fid}/tables`: page (1-based), unrotated source bbox, backend, expected_sha256.

The existing CAD conversion, Docling extraction and browser regression routes
are reused. Narrow or closed-source upstream utilities are documented in the
project-map branch research; they are not silently installed as mandatory core
dependencies. In particular free-during-beta binaries do not establish a stable
free local dependency. SCAD Office is distinct from OpenSCAD and industrial SCADA.

## R4 result contract

Manifest kind `ENGINEER_OS_LIRA_RESULTS_EXPORT`, schema 1. Exact ten-column TSV
members `values_00001.tsv` etc. Requests 1–4 and 8 may carry finite EXPORTED
values; 5–7, 9 and 10 remain availability diagnostics. Zero is a valid result,
not missing data. Per-part observations are separate from whole-run claimed
counts. Request counters must cover observed part rows, including successful
earlier chunks when a later chunk becomes UNAVAILABLE. Hashes, paths, encoding,
column framing, part sizes and counts are checked before interpretation.

Reader implementation does not merge the unqualified PR102 vendor exporter into
the application, execute a solver or grant acceptance. Real RES export and
qualified model/result correspondence remain a separate validation step.

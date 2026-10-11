# Optional local PDF viewer and desktop window

The regular application remains available with `python scripts/run_local_app.py`.
Neither option below requires a paid API or changes original source files.

## Original PDF preview

The UI calls `openPDFViewer(bytesUint8Array, sourceSha, caption)` after fetching an
original PDF through the authenticated local file route. `closePDFViewer()` closes
and cancels the preview. The viewer is a read-only canvas modal with page controls,
zoom, Escape/close and the original source SHA-256. It does not grant engineering
acceptance or verify extraction coverage.

The bundled renderer is the official npm `pdfjs-dist` version **5.4.624**:
`https://registry.npmjs.org/pdfjs-dist/-/pdfjs-dist-5.4.624.tgz`.
Tarball SHA-256: `5c387457cd03cc2e7b9c9b1ed642e8148d1ba44c3b8e5b5b771526feb24b61b9`.
Only `build/pdf.mjs`, `build/pdf.worker.mjs`, and the Apache-2.0 `LICENSE` are copied.

| Bundled file | SHA-256 |
| --- | --- |
| pdf.mjs | e668546e4f396e7769e141b7b0d09aed91c84e1752c7642a2fe87f335dfab84f |
| pdf.worker.mjs | a6a52b63b21b901a70c28d662c72716df14ffbfc4b54436747df333add0649cb |
| LICENSE | 0d542e0c8804e39aa7f37eb00da5a762149dc682d7829451287e11b938e94594 |

No CDN or network font/WASM files are used. PDF JavaScript, actions, XFA, forms and
annotations are not exposed or executed. Eval is disabled. A dedicated local
module worker parses bytes. Only one page renders at a time. Rendering is capped
at 4,000,000 canvas pixels and 4096 per side; input is capped at 100 MiB. Zoom can
therefore reach a resolution limit. Complex pages can still take significant CPU
and parser memory. Password-protected and malformed PDFs report an unavailable
preview; original bytes remain unchanged. Missing optional font/CMap/codec assets
can reduce fidelity for some PDFs; use the original file in a trusted PDF reader
when needed. Canvas rasterization is not text search or a complete accessibility
transcript.

Serving integration requires `/pdf-viewer.js`, `/vendor/pdfjs/pdf.mjs`, and
`/vendor/pdfjs/pdf.worker.mjs` as local JavaScript; CSP allows same-origin scripts,
workers and connections. All viewer layout rules live in the existing external
stylesheet. No `unsafe-inline`, `unsafe-eval`, remote worker or remote asset rule
is needed.

Run the Chromium test after installing development dependencies and Chromium:

```sh
npm --prefix e2e ci
cd e2e
npx playwright install chromium
cd ..
node tests/pdf_viewer.test.cjs --dom
node tests/pdf_viewer.test.cjs
```

The test uses a temporary loopback HTTP harness with a strict CSP, verifies DOM
controls and async teardown using a renderer mock, then renders a real two-page
PDF with the bundled renderer and checks that its embedded JavaScript is not run.

To test a separately supplied original PDF, without adding it to the repository:

```sh
PDF_VIEWER_SOURCE=/absolute/path/source.pdf node tests/pdf_viewer.test.cjs
```

This additionally renders the first and last pages, checks source SHA-256 display
and reports the byte/page counts. It does not validate every page or establish
source/extraction completeness. `PDF_VIEWER_SCREENSHOT=/absolute/path/image.png`
optionally captures the last-page viewport for visual review.

## Desktop window

Use Python 3.12+ and the existing project virtual environment:

```sh
python -m pip install -r requirements-desktop.txt
python scripts/local_desktop.py
```

`--data-dir`, `--selection-file`, and `--port` work as local startup options. The
default port is 0 (a free loopback port). Close the window to stop the HTTP server
and worker. Shutdown waits for in-flight worker calls before releasing the same
exclusive data-directory lock used by browser startup. History and originals are
kept in the existing Store. An already running backend using that directory must
be closed before launching this wrapper.

This wrapper reuses `make_server`, `Store`, `LocalModel`, `Worker`, and `DataLock`.
It creates no second data store, backend protocol or native JavaScript API bridge.
The model provider and model name follow the existing local settings. pywebview
uses the operating system's web engine; platform prerequisites (WebView2 on
Windows or GTK/WebKit on Linux) may need to be installed. A physical desktop
window must be verified on the target OS; a headless Chromium test is not that
verification. Runtime has no forced cloud dependency; package installation itself
requires obtaining the optional dependencies.

## Optional mesh visualization

`requirements-visualization.txt` pins PyVista 0.46.4 as a separate optional local
extra. It is not imported by the core application or required for PDF/CAD intake.
Installing it does not enable engineering solver verification or establish
original DWG/mesh equivalence.

# Stage 2 — actual document analysis quality, 2026-10-06

Stage2 is complete as a representative quality assessment with known limitations.
The representative quality check covers native PDF, raster text, native/scanned
tables, actual V4 page15 and graphical page500. It establishes what is correctly
read, omitted, or blocked. It is not acceptance of the 534-page V4 document.
No normative edition, calculation or geometric relationship is validated here.

## Source → extraction → response

| Case | OCR/extraction seconds | Page result | Source comparison |
|---|---:|---|---|
| Controlled native text | 8.28 | UNCERTAINTY,3 blocks | Three source lines preserved |
| Controlled raster text | 2.42 | UNCERTAINTY,4 blocks | Word «Число» omitted; height4m,2floors,brick,date preserved |
| Controlled native table | 2.94 | UNCERTAINTY,4 blocks | Three labels and three values preserved |
| Controlled raster table | 3.79 | UNCERTAINTY,4 blocks | «Этажи» → «ижее»; numerical values retained; label unverified |
| Actual V4 page15 | 7.33 | UNCERTAINTY,25 blocks | Five weather values and units match source text |
| Actual V4 page500 | 83.00 | BLOCK,FAILED normalization,0 retained blocks | OCR59 texts/1table/2pictures; table structure cannot be normalized |

Times include production Worker and journal writes, not just inference. All six
extraction queues completed SUCCEEDED; page500 still FAILED/BLOCK. Queue success
is not page validity. High-water process RSS reached3108.7MiB. The optional
Linux environment matches requirements-ocr-linux-cpu.lock and uv pip check.

Production LocalModel/Qwen3-8B Q4_K_M then analyzed the real persisted OCR through
the automatic page-batch route (cached completed extraction reused):

| Model case | Seconds | Checked result |
|---|---:|---|
| Raster text |57.52| Four expected facts, uncertainty; no false claim OCR was not run |
| Raster table |105.86| Damaged label explicitly unclear; value2 not invented as floor count |
| V4 table, Docling route |79.12|0.50kPa,0.30kPa,−30°C,+40°C,0.40m; no norm/calculation acceptance |

All three CHAT tasks and automatic batches completed; UNCERTAINTY,
acceptance=false, FINAL AUDIT NOT_RUN. This is actual OCR text, replacing the
earlier reconstructed-label fixture. OCR and Qwen processes are separated to
fit the8GiB environment; this verifies the production persisted-extraction
reuse route, not a simultaneous OCR/model memory guarantee.

## Graphical failure localized

The source is a drawing with a legend, not a verified rectangular numerical
engineering table. Docling exported its legend as14×3 with22 cells and a merged
cell. The production table validator raised exactly
`table cell is missing, merged or ambiguous`. A historical raw checkpoint and
fresh conversion agree on this failure. Conversion produced content; it was
normalization that rejected the ambiguous grid.

Visual comparison used a high-resolution source legend crop. Only9 of24
expected legend codes occur exactly in raw OCR. This is a label benchmark,
not a full character-accuracy score or proof of drawing geometry. The page
remains BLOCK. It must not establish actual defects or dimensions from these
labels alone. Retained output is empty, acceptance=false.

The journal now gives a fixed `TABLE_STRUCTURE_UNVERIFIED` diagnostic for
allowlisted internal table errors. Unknown exceptions remain generic
`PARSE_FAILED`; paths, source text and arbitrary error messages are not exposed.
No merged-table guard, source hash guard or acceptance rule was weakened.

## Current OCR metadata repaired

Live Qwen initially repeated a stale upload-preview flag, saying OCR had not
run although current batches came from Docling. CHAT and CORE_RUN now receive
current backend/page/blocked/failed/OCR metadata; role context saves the same
metadata. Preview-unavailable notes are excluded from those automatic contexts.
The actual OCR state remains REQUESTED_NOT_VERIFIED: execution is not proof of
quality. Native blank pages remain disclosed from the current journal.

Both mode-specific regressions were observed RED→GREEN. An independent review
found the remaining CORE_RUN path; its regression failed first, then passed
after the fix. Full343 Python tests,4 Node tests, compileall and diff check pass.

## Offline verification

All six cases were repeated in a fresh process after
ORT_DISABLE_TELEMETRY=1 and HF telemetry opt-out, with local prefetched weights
and HF offline. Linux seccomp denied socket/connect/sendto/sendmsg/sendmmsg
before OCR-library imports; a socket creation probe failed with PermissionError.
Zero Python socket-connect attempts were observed. This guard is specific to
this QA process; it is not claimed as a deployed Windows firewall.

The official weights were prefetched with Docling's download utility. RapidOCR
ModelScope prefetch needed a longer download read timeout; runtime/model-call
timeout stayed180s. Download/setup and initial runs are not conflated with
offline parsing. Seven model-artifact hashes are recorded in the QA JSON.

## Boundaries and handoff

OCR quality is measured, not declared perfect. Damaged table names and drawing
labels require source review before evidence; full-document coverage and
continuation are stage3, evidence/ТЗ connection is stage5, accepted engineering
case is stage7. Preferred Russian OCR is tested; bilingual switching and
different hardware are not. Windows stays stage9. Main/deploy are unchanged.

An initial model attempt hit a full scratch disk due to temporary weight-copy
files. Owned temporary copies were removed; verified originals/models and
source documents were preserved, SQLite integrity check returned ok. Final
measurements above are the clean repeat, not the interrupted attempt.

[Machine-readable quality matrix](../qa/2026-10-06-stage2-quality.json).
[Earlier successful native CORE_RUN](core-cpu-profile-2026-10-06.md).
Full real-source pages, PDFs, raw OCR and prompts are not published.

## Final live CORE_RUN on actual scan OCR

Production LocalModel/Store/Worker completed both specialist roles on the actual
controlled scan: 250.25s total, calls 119.36/130.84s; UNCERTAINTY, queue SUCCEEDED,
acceptance=false, FINAL AUDIT NOT_RUN. Saved role context reports DOCLING and
REQUESTED_NOT_VERIFIED, not old upload-preview OCR flags. The Ollama process-tree sampler returned an implausibly small0.4MiB and did not
establish runner visibility; it is marked unreliable, not presented as model
RSS. OCR process RSS above is measured. cgroup oom/oom_kill snapshot remained0.
A reliable model RSS peak for this repeat is not established.

The three stage2 requirements are satisfied: real model/OCR exercised across
all representative kinds; source/extraction/response compared with omissions,
time and memory recorded; controlled golden cases and actual V4 pages tested.
Quality failures stay explicit. Proceed to stage3: large-document continuation
and coverage; do not convert this development-stage completion into V4 ACCEPTED.

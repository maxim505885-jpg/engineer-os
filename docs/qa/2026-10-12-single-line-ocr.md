# Selected-line OCR qualification, 12 October 2026

An explicit "one line" profile (Tesseract PSM7) is added to the existing PDF
region API, UI and CLI. Default block PSM6 and sparse PSM11 remain unchanged.
The selected profile is preserved in the request, OCR dossier and history;
source pixels are unchanged. CLI identity now reports the actual render scale
from the dossier instead of a fixed6 when a long selection requires a smaller
scale. No automatic profile selection, text substitution or acceptance occurs.

The exact source crop of drawing page18 level +46,740 previously produced
"+46,740" plus a false second row in block mode, or a wrong digit/slash in
sparse mode. Single-line mode returns +46,740 without duplication on the same
pixels. A source-SHA/page/bbox/PNG-bound fixture is retained as JSON/base64 in
tests/fixtures/ocr/level-plus-46740.json, with no surrounding source document.
Genuine local OCR and authenticated/history-reload tests verify its sign and
literal text. The browser regression verifies selecting and binding the profile
with native-only reading; it does not claim OCR when language models are absent.

Six visual source regions, independently retained from the previous pass,
produce1/6 strict whitespace-only matches with PSM6,2/6 with PSM11 and3/6 with
PSM7. These are profile-specific results, not an automatic best-of score or full
document coverage. Negative0,450 with intersecting frames and the italic Cyrillic
labels remain problematic; no dictionary correction is applied. An independent
visual review confirms "Прогиб27мм" and "Прогиб20мм", with the final narrow,
slanted letterб somewhat unusual. Raw OCR continues to misread it in some cases.

Official tessdata_best rus/eng models at commit
e12c65a915945e4c28e237a9b52bc4a8f39a0cec were compared on the exact PNGs.
The repository licenses all its data under Apache2.0:
https://github.com/tesseract-ocr/tessdata_best/blob/main/README.md
The models did not improve the aggregate strict-match count for the six regions;
V4p55 OCR/native disagreements changed only41→40. They are not made default,
bundled into core or downloaded by the runtime. Model hashes and raw outputs
remain in the separate QA records; model presence is not quality qualification.

Stage13 remains OPEN for original Word reference/fonts/layout/fields/formulas,
remaining literal OCR errors and full graphic/raster/mixed associations plus a
qualified representative corpus. No user-PC update, engineering acceptance or
deferred solver/RES execution is claimed.

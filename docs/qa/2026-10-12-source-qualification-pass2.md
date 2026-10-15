# Stage13 source qualification — second pass, 12 October 2026

Two reproduced defects are fixed without treating extracted content as accepted
evidence. Complex Word fields now remain marked FIELD_NOT_EVALUATED across
paragraph/table-cell boundaries, including nested fields. Marker-only paragraphs
are retained. Malformed ranges receive FIELD_STRUCTURE_UNVERIFIED rather than
an invented boundary. On the original DOCX (SHA256 b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5),
all prior logical units and text remain; one field-boundary-only unit is recovered.
The source has 71 instruction fragments. Fields are not evaluated.

PDF region/native/table and OCR reading no longer call set_rotation(0) on
already unrotated pages. On twelve identical requests from two actual drawing
PDFs, redundant metadata writes previously caused 5,976 MuPDF object-out-of-range
diagnostics; the fixed route produces zero such diagnostics and identical OCR
text. Nonzero rotation handling and CropBox coordinate contracts remain covered
by the existing tests. Source bytes are unchanged.

Six exact raster crops were visually transcribed: drawing p18 levels +46,740,
-0,450 and -4,200; geodesy p13 title and "Прогиб 27 мм" / "Прогиб 20 мм".
With PSM6 and PSM11, only 3 of 12 complete OCR outputs match the transcription
after whitespace-only normalization. A correct number buried in unrelated
characters is not an exact region match. Wrong characters, missing signs and
extra text remain explicit unqualified output. These cases are an expandable
source-bound corpus, not full drawing/document qualification.

The DOCX font table declares 27 families, with no embedded font parts. The
local fontconfig selects substitutes; the table is not a list of all used fonts.
Exact original Word rendering, pagination, fields and mathematical/visual
equivalence are unverified. No original Word reference render is available in
this environment. This pass therefore does not close Stage13, grant engineering
acceptance, update the user's PC or run deferred LIRA/SCAD calculations.

Raw source-crop receipts, images, strict comparisons, font/field inventory,
RED/GREEN logs and final verification are retained in the Stage13 QA archive.

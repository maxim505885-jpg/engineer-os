# Original DOCX completeness supplement — 2026-10-05

Document remains BLOCK; no acceptance. Source SHA256: `b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5`.

The original Word source has **642 media members**, not just the 631 members with recognized image headers previously inventoried. Types: 369 PNG,115 JPEG,9 JPG,138 EMF,11 WDP. WDP decoding is unverified; EMF header recognition does not prove full rendering.

Recovered all **21 PBrush OLE native BMP payloads** by read-only stream parsing, without activation. Container/stream/payload hashes and original XML relationship locators were retained. Independent file checks verified 21 BMP and 21 derived PNG assets. These are drawings, not a confirmed higher-resolution ToR source.

Preserved **41 Office Math expression XML fragments**, including fraction/subscript structure and 298 math text tokens. The previous w:t text extraction excluded these m:t tokens. Exact XML fragment hashes and original element locators were rechecked. Mathematical semantics and calculation correctness are NOT_RUN.

Compared 157 PDF image occurrences on pages10,78,86,99,106,171, including page-frame components, with same-sized decoded PNG/JPEG/BMP source rasters. No exact pixel matches. Same-sized candidates on pages78,106,171 have mean absolute RGB differences3.91,2.67,1.82 out of255. Similarity does not establish source equivalence or completeness.

After explicit user authorization following the earlier security-review rejection, a controlled four-line ToR probe completed with RapidOCR and existing Tesseract using the official Russian tessdata_fast model. Both produce inaccurate text at source glyph heights3–5px; RapidOCR confidences0.38–0.55. Execution succeeded; accuracy remains UNCERTAINTY. No OCR result was accepted as evidence. Model commit87416418657359cb625c412a48b6e1d6d41c29bd; rus.traineddata SHA256e16e5e036cce1d9ec2b00063cf8b54472625b9e14d893a169e2b0dedeb4df225. No global Python package installation or application dependency change.

Source extraction checkpoints retain exact fragments and assets. This supplement changes audit documentation only. No source values, engineering gates, Evidence Register/Supabase records, main branch, merge or deployment changed.

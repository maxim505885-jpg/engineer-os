# Explicit local printed-label preprocessing

Bounded extension of selected source-region OCR, base cdd0cdd (PR142). User authorized remaining OCR fixes in one continuous pass. Existing optional local Tesseract/rus+eng and pinned Pillow; no extra runtime dependency or network/model downloads.

Cause demonstrated on original source crops: frame/arrow and adjacent clipped labels contaminate single-line input; narrow italic glyphs confuse б/д. Explicit `padded` adds20white pixels; `italic` retains dark neutral ink, applies fixed0.1 horizontal shear and20white pixels. No lexical correction, character whitelist, automatic selection, source mutation or acceptance. Preprocessing only with selected bbox, OCR enabled and PSM7. User must select the literal line without adjacent labels/frames.

Original exact PNG retained; derived PNG/hash/source PNG binding/fixed transform recorded and revalidated from original on save/reopen. Word boxes mapped through inverse transform to original unrotated crop-relative coordinates. Default original6/7/11 unchanged. UI shows both snapshots; colored details can be lost from derived input, which is not source equivalent.

Real source fixtures: Графика03.09 p18 −0,450 bbox[335.5,1376,368,1385] padded; Геодезия03.09 p13 Прогиб27мм bbox[327,295,374,304] and Прогиб20мм bbox[316,357,360,366] italic. Source/PNG identities stored in JSON fixtures. Tests require actual local models for literal recognition; skips must be stated. Wider prior selections are different scopes, not claimed fixed by these narrower probes. All statuses remain unverified, evidence0.

Stage13 remains OPEN pending original Word reference/fonts/layout equivalence and complete qualified graphic/raster/mixed semantic corpus. These three labels do not qualify every page. LIRA/RES postponed.

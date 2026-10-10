# Stage 13 — final scope gate for the local application

This report separates evidence established by source-level checks from tests of the actual Windows/local browser app. It is a test plan and blocker record; **not an ACCEPTED certificate**.

## Verified
- Core tests and Windows runtime CI were successful for merged PR129 `c52cfb49dee030ce6d98ae3fe69477964f42b57c`.
- Existing real Chromium UI test uploads a synthetic PDF, previews original and confirms file survives browser reload.
- Production `persist_selected_unverified_asset` routes explicitly selected PDF table/DOCX OMML or embedded-media candidate through hash checks to a dedicated restricted Supabase RPC, apart from validated text.
- Live V4 source-vs-Supabase checks confirm 3 saved candidates: 1 table PDF, 1 DOCX OMML, 1 DOCX EMF, all status UNCERTAINTY.
- Full DOCX V4 source asset candidate inventory: 41 formulas and 654 media, 695 total, but only 2 DOCX candidates committed to DB.

## New regression
- PR130 extends real Chromium UI test with DOCX upload and persistent file card after reload. Do not mark this PASS before PR130 Core/Windows CI is successful.

## Remaining acceptance blocker
- The local browser server handles file upload and reload independently of the asset candidate RPC. There is no demonstrated **single user-visible flow** from uploaded real PDF/DOCX through extraction, explicit unverified candidate selection, Supabase candidate save and query/readback, then display on reload.
- Synthetic UI fixture does not demonstrate full 534-page PDF processing or DOCX image/formula semantic accuracy.
- Full V4 visual fidelity is a separate document-qualification gate; 40 vector-only sheets require manual/visual confirmation and must remain BLOCK until verified.

**Stage 13 software-module gate: BLOCK for full UI/end-to-end integration.**
**V4 engineering source-accuracy gate: BLOCK independently.**

## Required next implementation
Connect an explicit user-approved "save as unverified candidate" action into the local upload UI/backend using source hashes, and show the stored candidate with UNCERTAINTY after reload. Keep RPC server-only; never return service-role credentials to browser. Implement one Chromium regression covering PDF and DOCX candidate selection → server-backed write → readback → reload, including negative hash/identity. Do not auto-accept OCR/text/graphical assertions.

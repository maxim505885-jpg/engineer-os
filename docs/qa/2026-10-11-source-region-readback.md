# Stage13 selected source-region readback — 2026-10-11

True V4 source:74,522,583bytes, SHA256 b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916. Originals unchanged.

## Implemented

Authenticated local POST selected PDF region → disposable bounded worker → native words + source PNG + optional local rus+eng OCR. PSM6 for text blocks, PSM11 for scattered labels. Page/selection/hash/status/raster/dossier are validated before append-only SQLite persistence; reread checks source and saved result integrity. GET history survives Store reopen. Shared2 slots, source/result/history size caps, process deadline and descendant termination. No evidence or acceptance is created.

UI supports individual detected-cell selection and manually selected graphic region, side-by-side candidate text and source image, preserved conflicts, saved history reload. Detected values are never overwritten automatically.

## Actual source findings

48 pages/788 old cell differences independently reproduced. Detector serialization loses0selected nonspace characters and adds0; same-flags/native-center geometry matches788/788. Default clipping, glyph boxes, and fill/stroke merging explain differences; naive clip replacement would introduce neighbor-row text and duplicate labels. This verifies serialization only, not full table semantics.

Real authenticated HTTP selects p493 raster legend and p534 numeric/level graphic regions; saved hashes, PNG and actual OCR input raster, history read/reopen, unchanged original, zero new evidence verified. PSM11 recovers p534 −0,450/44/38 where PSM6 failed. Pairs17/8,19/11,20/13 and raster П1 are not fully recovered; errors remain candidates. No geometric/engineering association is inferred.

Controlled scanned-only and mixed tables exercise actual OCR expected values; mixed native/OCR disagreement is retained. Independent review reproduced three protocol/process/source-boundary defects; they were fixed with safety regressions.

## Status

Stage13 remains OPEN: full semantic/visual source qualification, mixed/raster table relationships, exact Word/font/formula layout and representative qualified corpus remain incomplete. Store/model inference of full original report is not rerun here. User PC installation not performed. Calculations remain deferred.

DOM regression reproduced readback loss when the1500ms refresh replaced active controls during a delayed1800ms region response. Source-asset controls are now retained per file/session and cleared on session switch; completed readback remains visible.

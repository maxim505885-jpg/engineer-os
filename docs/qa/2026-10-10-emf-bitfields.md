# №13 — masked EMF raster source coverage, 09–10.10.2026

Base candidate ebcafaa69c1a715f3e969fbcf1aa614f2e115533. Calculations remain deferred.

## Actual omitted information

Original DOCX: 147210288 bytes, SHA256 b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5. word/media/image465.emf has EMR_BITBLT at byte54676, BITMAPINFOHEADER40 plus three DWORD masks (52 bytes), BI_BITFIELDS3, 32bit,17x19. It was explicitly unavailable in PR106. The original logical parent12572 has54282 chars; Store20000 limit also prevented image preview under the previous strict quote binder.

## Implementation and bounds

Read explicit RGB555/RGB565/RGB888 mask profiles for16/32bit BI_BITFIELDS with a40byte header+12mask bytes. Validate mask depth, nonzero, contiguous, non-overlapping channels; unsupported profiles remain unavailable. Preserve record offsets, masks, payload SHA and exact revalidation. Previous bitmap/package/pixel limits are unchanged. No alpha inference, GDI execution, transforms, crop, ROP/compositing or full EMF/Word rendering.

Image-only source binding now allows a TEXT_LIMIT-flagged exact original text prefix after the same session, child source, original SHA, parser identity and full locator revalidation. Image binding explicitly source_confirmable=false. Quote office_location and engineering candidate gates continue rejecting clipped text. Forged prefix/locator/truncation state fail closed. Original asset and selected payload SHA are checked again before PNG.

## Real-source results

All120 discovered bitmap sources in138 original EMF assets decode. All29880590 RGB pixels match an independent BMP-wrapper/Pillow BMP decoder in full arrays; no perceptual threshold. Native reader14684 logical units/671 image refs preserved. Original SHA unchanged. This establishes source-pixel extraction only, not complete visual document coverage.

image465 asset SHA256 9c860342997b4c393fa77e8c85ea9e7e2f080804cd63872290972b0a61360ece; raster RGB SHA256 4aeb840401b2942dd782b70db5c08b363237e8ed4750ff9be54f56a58d9a9969; payload SHA256 ae0cfc636d8099e438cd8ee6f30d11a1c00133786d6bab606893f01818297110.

A derived isolated DOCX containing the exact original image465 asset passed controlled Store/Worker/model/receipt/source binding/PNG. Stored20000 chars,text_truncated=true; PNG17x19 matches above RGB SHA; strict quote remains blocked; acceptance=false. This is an isolated source-asset fixture, not the original logical parent or full original Store/model run. A controlled browser fixture covers both normal and masked raster ordinals with explicit unrendered scope.

## Independent review

No Critical/Important/Minor defects found in decoder or clipped-parent fix. Exhaustive65536 pixel values for each16bit555/565 matched direct mask scaling. Review ran25 decoder/native tests, then28 bitfields/bitmap/Office tests. RED regressions reproduced omitted mask-format metadata and clipped-parent preview failure before fixes. No fabricated engineering finding or ACCEPTED result.

## Remaining scope

№13 stays open,8✅/8🟡/3❌. Full EMF vector playback, Word placement, full rendering, raster/mixed tables, OCR conflicts, formula visual correspondence, full V4 and qualified corpus remain open. Physical user PC not updated; no engineering acceptance. Next independent step: full mixed-graphics/table visual coverage with source-bound rendering. LIRA/RES remains deferred.

## Publication and local verification

PR107 OPEN,head21114ab273a5927f34af985126afb0a804f6b422,tree7898926d5b8121e655a0b16ccdaf904c7b136dee matches tested local tree. CI/merge pending.851 tests/99.990s OK,17 environment skips;38 focused,10 Node,2 HTTP/DOM,5 Chromium PASS. Architecture/compile/JS/diff PASS. Initial DOM session-switch timeout passed on rerun, root cause not established. Windows49 suite execution pending.

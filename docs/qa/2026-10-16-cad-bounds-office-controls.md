# CAD hash bounds and Office isolation controls — 2026-10-16

Baseline: `d472dee1c2b4cb924f0efc5b50d8c9a7de80063f`, existing draft PR #155.
This package changes CAD file-identity handling; it does not qualify Office layout,
DWG fidelity, vendor results, real engineering acceptance or a release.

## CAD correction (T08)

Four synthetic regressions were observed before the implementation:

- An oversized converter derivative reached `Path.read_bytes` before its size gate.
- Growth of the original during conversion caused an unbounded final read.
- Removal of the original raised from `finally`, losing the conversion receipt.
- Mutation after inventory could retain conversion PASS when the terminal EOF
  remained intact. The regression actually returned PASS before the correction.

CAD file hashing now streams within the existing 20 MiB limit and checks size,
mtime and file identity around the read. Staged and final original identities use
that helper. An oversized/changing derivative is blocked before inventory. Source
removal/growth retains a BLOCK receipt with `source_unchanged=false`. The derivative
is hashed again after inventory before conversion PASS; changed bytes receive an
explicit CONVERTER_OUTPUT_CHANGED ledger entry. Tail reading is limited to 256 bytes.

No source repair, budget increase or DWG equivalence authority was added. Existing
subprocess log capture and process-resource limitations of the optional conversion
CLI are not closed by this patch. The earlier five real DWG probes used the separate
existing AppContainer primitive and remain negative qualification results.

Verification: four new regressions RED then GREEN; full CAD scope 48 tests OK.
Fresh full native regression: 1371 tests in 395.672 seconds, OK, 34 skipped.
Architecture guard, repository guard and pip check passed. No browser UI changed.
Independent scoped code review found no actionable regressions. The reviewer's
sandbox could not run the synthetic tests, so independent test execution is not
claimed. No whole-product acceptance follows from this software verification.

## Office diagnostic controls (T03/T04)

All engineering document bytes came only from the controlling source folder.
Private derived files, source hashes, screenshots and diagnostic guest receipts
remain under `.engineer-os/tzz-stage2` and are not published.

The three neighboring source PNGs all have valid PNG chunk CRCs. A simple DOCX
containing their unchanged bytes rendered all three through the unchanged v4
bundle. This does not reproduce a PNG decoder failure.

A separate disposable Linux guest converted the original DOC to diagnostic DOCX,
without a NIC or host shares, using read-only hashed input transport and the same
contained host runtime. Its diagnostic worker and seed have separate identities;
it is not a production renderer bundle. All three PNGs survived with exact RGB
pixel identity and valid relationships. The first two occur as inline images in
one paragraph. Original source preservation was verified.

Re-rendering that full diagnostic DOCX through v4 still omitted the second raster.
A small grouped-versus-separate control displayed both images in both arrangements;
grouping alone does not explain the full-document failure. The control repeated
DrawingML docPr IDs across its two arrangements, so it is exploratory and not a
standalone conformance qualification.

Moving the second image run into a separate paragraph in a private variant restored
that image but omitted the third expected source raster instead. Repeating the
single split with namespace-preserving XML editing gave the same two visible target
images. Neither variant is accepted as a fix. The simple whole-document save/reload
and paragraph split do not establish a qualified production route.

A reduced document retaining imported styles/settings/section failed the render
protocol. Its guest failure detail was not captured by the first diagnostic script;
the cause of that failed control is UNKNOWN. It is not source corruption evidence.
Further reductions must preserve exact fixtures and record failure diagnostics.

The known missing-raster and frame/footer failures remain BLOCK. There is no
original-equivalence, all-object fidelity, normative verification, solver run,
responsible review or FINAL_AUDIT claim.

# Browser CI correction and private SCAD API compatibility — 2026-10-16

Baseline: `8c3c95ce0ab607e2d88dc1d4f314944b05ac6366`, existing draft PR #155.
The published product correction remains the bounded CAD hash/receipt change.
This follow-up changes a browser test and records private vendor investigation;
it does not enable a production SCAD adapter or qualify a calculation model.

## Exact-head browser failure and correction

Core run 38888137378 and Windows run 38888137366 failed in the existing main
Chromium smoke. Logs from both jobs showed the same strict-mode selector failure:
a session button and an SPU project card share the project title. The global
button-by-name locator was ambiguous. This reproduced locally before correction.
After scoping the desktop selector, the test reached a second outdated expectation:
it required the old workflow bar, deliberately hidden by the reused SPU shell.
The mobile overflow assertion itself passed; no layout fix was warranted.

The test now selects the desktop conversation through its named navigation and
uses the visible SPU project card on mobile and restored mobile history. It checks
the actual visible SPU navigation, clicks its calculation route and confirms that
the target panel opens. Original upload/history/isolation/cancel/retry/backup/
restore assertions remain. No application UI, styles or acceptance logic changed.
All seven local Chromium browser workflows passed after this correction.

The earlier full native result remains 1371 tests OK, 34 skipped, on the CAD
product tree. The subsequent change is browser-test-only; a new whole Python run
was not needed. New exact-head CI must still be checked after publication. A green
local browser run is not a claim that the hosted failures have already cleared.

## Private installed SCAD API investigation (V01)

Only the controlling source folder supplied engineering model bytes. Installed
SCAD Office headers, the SDK PDF and DLL version 21.1.9.7 supplied the software API
contract. No external engineering/normative sources, new paid service, application
installation, solver execution or native project write was introduced.

A private C# probe used documented Create/Read/getter/Release methods on copied
SPR files. A first zero-capability AppContainer probe failed before ApiCreate with
DllNotFoundException. Static DLL dependency names identified the installed VC90
CRT/MFC dependency. An explicit private activation-context manifest referencing
already installed amd64 VC90 assemblies resolved that loader failure; no Windows
DLLs, registry, installed runtime or licensing configuration were modified.

All three current SPR files then returned ApiCreate=0, ApiReadProject=0 and
ApiRelease=0 through the existing AppContainer/Job runtime boundary. The probes
had zero capabilities, fixed time/process/memory limits and a 2 MiB output budget.
Original and staged bytes and the copied runtime manifest remained unchanged.
The private outputs are process-hash-bound and retain `acceptance_granted=false`.

Selected PROJECT data were read through the documented API: node coordinates,
element connectivity/type/rigidity indices, raw support/deletion masks, API units
after project read, raw force records, combination coefficient arrays and native
rigidity descriptions. Two read-only passes agreed on geometry/connectivity/units.
Host checks confirmed finite coordinates/force values, in-range node references,
matching declared load/combination counts and source/output identity. Bounded API
messages were captured; their lists were empty at the capture point.

The installed vendor API manual (pp. 5–6) defines the three unit slots as linear
dimensions, bar-section dimensions, and forces; its coefficients convert those
quantities to metres and tonne-force. All three current SPR reads returned the
same API tuple: `M/1`, `M/1`, `H/9810`. This qualifies the documented API slot
mapping and declared coefficients for these three reads. The literal label `H` is
preserved as returned; no independent conventional-unit interpretation is claimed.

This is not complete model-unit qualification. The manual says to check and, if
needed, redefine the working unit system after reading a project. Correlation with
the source UI/protocol unit settings and interpretation of the actual force records
remain unverified, as do material/section semantics, joints/releases, local
axes/offsets, elastic supports, solver result packets and correspondence to the
actual structure. No native results or solver run are claimed. The historical
absence of SCAD inputs must not be applied to these current SPR files, but
successful getters do not establish production SCAD support.

All proprietary DLL copies, SDK/probe hashes, source/model data, compiled probes
and receipts remain private under `.engineer-os/tzz-stage2/scad-api-current/`.
No binaries, vendor header copies, source hashes or model payloads are published.

## Office control diagnostic update

An exact retry of the unchanged reduced styles/settings/section fixture captured
the previously lost failure detail: the guest reached RENDER_BEGIN, then reported
FileNotFoundError for the expected derived PDF. The guest process exited 0 through
its controller, but no valid result frame existed. This is a failed diagnostic
fixture, not evidence that the original DOC is corrupt. No limits were increased
and no production renderer/configuration changed. Missing-raster and frame/footer
qualification remains BLOCK as recorded in the preceding QA.


## Exact-head CI and further private controls

All hosted workflows on `4adaa0aa952adfac8bd7bf574f223a933d288737`
completed successfully: Core Tests (38890313526), Windows local runtime
(38890313309), Optional engineering adapters (38890313548), Repository Security
Guard (38890313533), and the PR workflow (38890310680). This qualifies those CI
checks on that commit, not the engineering corpus or release gates.

A private in-memory SCAD API exchange-unit control on the three current projects
checked 1120 nodes / 3360 coordinate components. Requesting a linear exchange
coefficient of 100 scaled the API coordinates by exactly 100 (maximum absolute
error zero); the force unit remained unchanged. No native write or solver was
called. This tests API exchange behavior only; it does not verify project UI or
protocol settings, force-record units, section semantics, model correctness or
production vendor support. The detailed private receipt remains under
`.engineer-os/tzz-stage2/scad-api-current/`.

An existing Word ProtectedView capture was matched to the current report source.
The source and captured main-story hashes match; all 69 EMF hashes and 69 raster
hashes match the capture/render manifests. Reuse required no new Word execution.
The capture has 69 pages, the supplied PDF 65 and the v4 derivative 68. The native
capture is itself unqualified and its original network isolation was not verified;
page counts alone establish no canonical layout. Native pages 7–9 visibly contain
all three assignment sheets, strengthening the missing-sheet finding for v4.

A preliminary native-cell text screen covered 552 captured cells: 364 substantial
text candidates occur in the PDF; 169 are too short to diagnose preservation,
18 are empty and one required visual follow-up. That candidate's text and restraint
diagram are visible on native page 56 / derived page 55; an inline-object marker
explains the literal mismatch candidate. No text loss was established there.
Frame/footer and line/color differences remain unqualified.

A separate imported-DOCX logical-cell comparison found 521 exact literal matches,
30 complex cells needing visual review, one extra empty imported cell and one
page-break-marker difference. There are 553 imported logical cells versus 552
captured Word cells. These are diagnostic results, not complete table, graphic or
numeric qualification. The cell JSON is associated with the captured reference,
but its hash was not included in the original native manifest; this provenance
limitation is retained privately. No renderer promotion or acceptance follows.

All 52 registered sources remain unchanged, with no additions/missing files on the
latest preservation check. Private payloads, source identities and receipts stay
outside Git. T03/T04, remaining V01 semantics and unproven release gates stay open.


A further private variant split the second inline image into its own paragraph and
added explicit page-break-before properties to the second and third image
paragraphs. It still renders 68 pages, with the first two assignment rasters visible
and the third absent. Explicit pagination is therefore not a qualified workaround;
no production changes were made. Root cause remains unresolved.

An imported-media census found 29 raster parts with exact decoded RGB matches in
the original v4 PDF, 51 without exact matches (33 JPEG, 18 PNG), and two WMF parts
excluded from this raster decoder. Nonmatches do not prove absence: recompression,
color conversion, cropping and scaling require separate visual/object checks.
These diagnostics do not close the 30 complex-cell or full-graphics qualification.

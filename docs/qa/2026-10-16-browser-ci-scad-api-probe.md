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

These are selected API data, not complete semantic qualification. Source UI unit
correlation, force-code interpretation, material/section semantics, joints/releases,
local axes/offsets, elastic supports, solver result packets and correspondence to
the actual structure remain unverified or excluded. The SDK specifically requires
checking units after reading a project; the API unit labels and coefficients were
retained without silently normalizing them. No native results or solver run are
claimed. The historical absence of SCAD inputs must not be applied to these current
SPR files, but successful getters do not establish production SCAD support.

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

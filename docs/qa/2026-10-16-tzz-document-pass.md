# New source set — real document pass and vendor-original intake

Latest user resumed point2 and requested continuous completion of all criteria.
Only the new exclusive source root is used for engineering inputs. Previous object,
ToR and source-bound results are not substituted for this new set.

## Verified results

-52files/106072451bytes;repeatSHA25652/52unchanged. Source census204PDFpages,
  804DOCXlogical units. No separate controlling ToR identified by native-text search;
  this is not proof there is no task in graphics or another source part.
-6uniqueDOC/DOCX read in separate owned Word Protected View instances.121EMF pages,
  then121PNG/0render failures in existing AppContainer GDI pilot. Source and snapshot
  hashes checked. Earlier multi-open failures retained privately;fresh instances and
  unique names captured all6. Protected View retained;ordinary open not used on sources.
-3DOCX independent logical-cell comparison:365literalMATCH,5complexvisual candidates,
  0missing/extra after mapping Word ordinal cells to source grid coordinates.
  All5complex cells viewed on source-bound pages2/14;schemes/dimensions visible.
  This is not mathematical validation or complete layout acceptance.
-40OMath references across3DOCX. Byte identities/visual representation are distinct
  from checking formula meaning. Source PDF page2 already shows unresolved symbol
  boxes;do not silently reconstruct their meaning.
-Real application pipeline on separate data:10PDF extraction cycles completed;
  Office attachment jobs253+253+298DOCXunits and928+190XLSXunits completed with
  0failed units. Parent extraction-only qualification jobs deliberately end without
  model inference;they are not successful model/CORE runs.
-Graphics-only PDF is an actual drawing,not empty. Existing bounded OCR emitted
  206unverified candidate blocks;source hash unchanged. No OCR number is accepted
  merely because recognition succeeded.

## Bounded product change

Original SPR/SEC/RTF uploads are now supported with empty preview,explicit
UNAVAILABLE/reasons,hash-preserved storage and download. No parser,Office or vendor
process runs during intake. Native extraction remains rejected for these formats.
This enables retaining the new files in a project;it does not verify SCAD semantics.

TDD:missing suffix RED;new tests and existing local_app suite24tests/OK. Real HTTP
roundtrip of7SPR/SEC/RTF from new root PASS,byte-identical download and attachment
content disposition. Independent scoped review found no important defect;reviewer
execution sandbox limitation is not counted as independent testPASS.

## Office isolation investigation

Automatic approval review initially rejected a third-party DLL IPC experiment.
The user then explicitly approved a separate-copy/control-only experiment.
Original runtime DLL SHA remains unchanged. Candidate binaries are private,
experimental and not enabled in application or shipped.

Changing shared PIPEPREFIX also changes a named mutex and failed control.
API controls demonstrated Local/LOCAL case behavior. Revised candidate changes
only PIPESYSTEM within its existing16-byte field,leaving mutex prefix unchanged.
Original and revised runtime both create/read back the owned normal-control PDF.
AppContainer full render still hit180s timeout with noPDF;owned job terminated.
Direct native local pipe and mutex controls succeed,but LibreOffice osl_createPipe
still returns false with/without current-security handle. Thus the production
Windows Office boundary remains UNAVAILABLE,not fixed by this experiment.

Private receipts/scripts:.engineer-os/tzz-stage2. No project originals or binaries
are committed. Remaining:production controlled Office route,complete layout/critical
object/font and cross-version qualification,source-bound task extraction/review.
Point2 remains OPEN until its criteria pass. Continue independent application work;
no unsupported100%/engineering acceptance/FINAL_AUDIT claim.

## Offline Linux feasibility control

Approval execution recovered. Verified private pycdlib1.22.0 wheel by SHA256;
created and read back NoCloud control seed ISO. Official Debian13 cloud image
booted using QEMU11.1.0 TCG inside Windows AppContainer (verified token1,
capabilities0),no virtual NIC,no monitor,no user engineering inputs.
Guest serial emitted the owned control marker and powered off normally;
QEMU exit0,no timeout,177.48s. Original downloaded image SHA512 unchanged.
Private receipts:linux-worker-spike/linux-boot-verification.json and referenced run.

Ruling: investigate an outer Windows AppContainer around software-emulated Linux
rather than enabling firmware virtualization;TCG itself is not the security
boundary. This feasibility control does not qualify Office conversion,host
file/network denial,active-content behavior,fonts,performance or release.
Next:software-only guest provisioning,then owned document/boundary controls
before any production integration or engineering-source conversion. Point2 OPEN.

## New-corpus native payload roundtrip

Independent ZIP/XML reference compared with actual application-store source
assets and Office reader on all three distinct new-corpus DOCX files. Matched
370/370 table cells (215 containing digits),40/40 OMML formulas and62/62
media/embedded objects;zero missing/mismatched objects and no unmapped XML
cells in the checked direct-table scope. All three source SHA256 unchanged.
Reference uses no entity resolution/network. Comparison receipts bind source,
reference and parser hashes. This is native payload preservation,not formula
correctness,layout equivalence,controlling task or full-document acceptance.
Private evidence:qualified-payloads-0f91dfe5ef9346758e40e7d2c75bc7d6/summary.json.

Software-only Linux provisioning and full application regression were started
as separate owned processes;their completion remains unproven until receipts
and final outputs are inspected. No user documents entered the build VM.

## Software provision and regression follow-up

Software-only Debian VM installed LibreOffice25.2.3.2 Debian build,Writer/Calc,
Python,bubblewrap and selected open fonts;package-install marker present,exit0,
357.65s,no timeout. No engineering inputs or shared host folders were supplied.
Package list is retained inside the build image;production manifest/export and
isolation qualification remain pending.

First offline AppContainer Office control reached Linux and exited normally,
but conversion did not start:private guest PATH omitted /usr/sbin so runuser
was not found. Corrected test script to absolute /usr/sbin/runuser;repeat pending.
A normal guest shutdown alone is not converter success.

Full Python regression:1312 tests,4 failures,34 skipped. All four failures were
CLI JSON Cyrillic decoding mismatches under PYTHONIOENCODING=utf-8 with locale
CP1251 decoding in subprocess.run(text=True). Setting PYTHONUTF8=1 consistently
for parent/child made the complete affected10-test module PASS. No product
change was made for this runner mismatch. Full UTF8 regression is running and
not yet counted successful. Preserve both initial failure and repeat logs.

## Contained offline Office control result

Direct Python UID/GID65534 drop replaced PAM-based runuser;result serial channel
separated from guest login terminal. One owned DOCX converted successfully to
one-page PDF:required heading,table labels and2500mm text present. Returned PDF
SHA256 matches guest output. QEMU exit0,no timeout,74.938s;AppContainer token1,
capabilities0,virtual NIC absent;guest interfaces list contains only loopback.
Build image SHA512 unchanged. No user engineering documents were processed.
Private evidence:linux-worker-spike/offline-office-control-verification.json.

This proves this synthetic offline conversion only. Remaining before production:
source-bound input/output protocol,host file/network canaries,active-content and
resource-limit checks,repeat/restart/cleanup qualification,runtime/package/font
manifest,integration tests and real-source layout/critical-object qualification.
The earlier runuser/combined-terminal attempt has no verified PDF receipt and
is not counted PASS. Point2 remains OPEN. Full UTF8 suite still pending.

## Firmware input,boundary controls and full regression

Full suite repeated with consistent PYTHONUTF8=1/PYTHONIOENCODING=utf-8:
1312 tests,408.971s,OK,34 skipped. Initial four encoding failures retained;
no product behavior was changed to mask failures. Log:full-suite-utf8-20261016.log.

Actual QEMU AppContainer controls:staged owned file load+boot succeeds(expected
exit33);unstaged owned file load fails(Permission denied,exit1);connection to
own live local TCP listener fails(exit1),while normal listener control connects.
These representative checks do not prove every possible network/file channel.

Owned DOCX transferred by read-only guest fw_cfg(no shared host folders),guest
input SHA256 matched host expected hash before Office invocation. One-page PDF
returned,hash verified and required text/table/2500mm preserved. Exit0,no timeout,
68.798s;AppContainer1/capabilities0,no virtual NIC. Staged source SHA unchanged.
Private evidence:linux-worker-spike/fwcfg-boundary-verification.json and receipts.

Remaining:bounded production protocol,active-content/limits/cancellation tests,
immutable runtime/package/font manifest,existing-app integration,source-specific
render qualification. Synthetic success is not real-document engineering PASS.

## Host renderer-result protocol

Added engineering/document_intelligence/office_render_protocol.py:bounded
six-line unwrapped-base64 result decoding,source/output SHA256 checks,strict
framing and duplicate JSON rejection,failed exit-result and PDF size/signature
rejection. Returned receipt explicitly DERIVED_UNVERIFIED,acceptance false and
PDF structure NOT_VALIDATED;no security assertion inferred from guest metadata.
Caller still must verify actual process exit,isolation/runtime and source state.

TDD:missing module RED,8 tests GREEN. Independent review found newline memory
amplification;new1MB newline-flood regression measured9.4MB peak RED. Early
separator cap and exact6-line framing fixed it;9tests GREEN,peak<128KiB.
Related qualification20/source-assets6 tests PASS;architecture guard PASS.
Final decoder also matches actual owned fw_cfg control PDF bytes.

Owned infinite boot control hit1s deadline;JobObject terminated QEMU with exit124,
profile cleanup HRESULT0,without touching user server/processes. Private receipt:
linux-worker-spike/run-396f4373b5604c159800b6b0602ef31a/receipt.json.
No production worker integration or real-document qualification claimed yet.

Review follow-up:LF/CR cap alone missed VT/FF/FS separators interpreted by
str.splitlines. All7 separator-flood variants were exercised;5 additional RED
cases reproduced. Byte-header precheck and literal LF parsing with explicit CRLF
handling remove that path. All9 tests PASS;independent reviewer confirmed fix
and reran9 tests PASS,no remaining important findings. Actual fw_cfg output
still decodes to the previously verified PDF.

## Reusable guest worker in project runtime

Added runtime/office_guest.py,with exact firmware request schema,64MiB source
cap,SHA256/signature checks,loopback-only guest-interface check and a dedicated
UID/GID65534 Office child. Per-job macro3/link2 profile,CPU/AS/file/descriptor
limits,150s timeout/process-group kill and NOFOLLOW regular-file bounded32MiB
PDF readback. Controller emits the existing source-bound result protocol.
The host must still provide qualified AppContainer/image/command/staging/serial
limits and cancellation;this guest file alone is not the security boundary.
DOC/DOCX/RTF signatures accepted by contract;only owned DOCX was exercised.

TDD4 input/command tests:missing module RED then GREEN. Independent review found
no important issues within disposable-guest scope;reviewer test cleanup hit a
Windows sandbox restriction,not counted as independent fullPASS. Product guest
script itself then ran inside real offline QEMU/AppContainer:exit0,no timeout,
67.605s,1page21,976byte PDF. Host product decoder verified required heading/table/
2500mm and hashes. Private product-guest-verification.json binds guest-code SHA.
This is a synthetic conversion,not full resource/active-content qualification.

Build identity now includes runtime source directory through the existing bounded
inventory. New runtime-mutation test RED before inclusion,GREEN after;complete
build-identity10 tests PASS. Independent review confirms manifest coverage,not
deployed-image identity. Remaining host integration/active-content/font/real
source qualification gates are unchanged;point2 remains OPEN.

Related Office suite38tests/12.234s/OK after guest-worker integration. Architecture
and repository guards PASS. Full1312-test success above predates this change;
no claim that the new worker has already passed a new full-suite run.

## Windows contained-process runtime

Added runtime/windows_contained_process.py:trusted caller command preflight,
exe-under-runtime and disjoint staging,link/path/limit checks,unique AppContainer
profile with zero capabilities,temporary ACL grants,minimal environment,owned
suspended process assigned to2GiB-process/3GiB-job/4-process JobObject before
token check/resume. Monitors cancellation,deadline and selected output bytes.
It is a process primitive;caller must separately qualify immutable runtime and
constrain every command/image/IO option. No document-facing API enabled yet.

TDD4 preflight tests PASS. Independent review identified asynchronous descendant
termination race;2 additional RED cases then bounded zero-ActiveProcesses wait
fix. Cleanup/readback fails closed if termination cannot be confirmed. Reviewer
confirmed fix,no remaining important findings;6 focused tests PASS. Build-identity
10 tests PASS,architecture guard PASS.

Real product-host controls after fix:normal own boot exit33,timeout exit124 at
1.109s,cancel exit124 at0.549s. Owned output flood rejected OUTPUT_LIMIT at
13,515 observed bytes with1,024byte polling threshold. This is a monitored
threshold,not a kernel disk quota;output can overshoot between polls.

Full synthetic chain using new Windows primitive+guest worker+host decoder
repeated after fix:AppContainer1/capabilities0,noNIC,exit0,no timeout,64.852s.
Runtime files/image hashes checked before launch;source/build-image unchanged;
returned1page21,976byte PDF matches required heading/table/2500mm text and hash.
Private product-chain-latest.json binds host/guest code and result provenance.

Remaining:configured document host adapter with immutable bundle/seed identity,
per-job source staging and output/cancellation integration into existing app;
active-content,package/font and real-source qualification. Point2 still OPEN.

## Configured adapter,queue and file UI

Added pinned-bundle verifier and application render adapter. Bundle identity
checks exact165-file set,all hashes,link/path/count/byte limits,current guest
source hash and externally supplied manifest pin. Private builder inspected
seed ISO and verified embedded guest script equals project runtime source.
Manifest pin:bcd3121f133f346f0bdca586bf268623fad773acf66aec65df0c1a3419f1f44a.

Adapter creates checked per-job source/image/seed copies;fixed noNIC/no monitor/
no host-share command;owned runtime timeout/cancel/output monitoring. Serial
bytes/hash must match process receipt;host decoder binds source/PDF hash. Original,
staged source and bundle rechecked after render. No host Office/cloud fallback.
Bundle4/adapter4 tests RED->GREEN;independent review:no important findings.

DOCUMENT_RENDER now uses existing ENGINEERING_RUN queue/API/Worker. Local
store-root office-renderer.json config only,not user-supplied API command/options.
Input classUNKNOWN,one DOC/DOCX/RTF<=64MiB. Original revision checked before and
after;derived PDF gets original fileID/hash,jobID and unverified lineage. No
accepted evidence. Queue3 tests PASS;existing engineering-jobs13 tests PASS.
Related Office suite49 tests/13.754s/OK. Independent queue review:no important
findings;derived preview caption corrected from original to PDF-copy.

Actual full adapter and actual queue/Worker owned-DOCX controls PASS,required
text/table/2500mm and source/PDF hashes checked. Chromium actual API/queue/Worker
UI control PASS with explicitly synthetic converter payload:button,derived file
labels,preview copy caption and no accepted evidence. Desktop/mobile screenshots
inspected;one bounded text/order refinement confirmed by final browser PASS.
Original supplied SPU untouched. Local default worktree app data configured
with pinned private bundle;other/main user data not modified.

First real new-corpus DOCX via actual queue and contained converter SUCCEEDED:
source35d267506adfabc901b8a5a974880dc2bd1f95d218b111375c34aa6c3529799b,
12-page738,289byte derived PDF,113.476s,AppContainer1/capabilities0,noNIC,exit0.
Original source SHA unchanged. Receipt:real-docx-render-receipt.json;PDF/file
lineage in separate render-real-docx-qualification store. Page count is not
content/layout/math qualification;those gates remain OPEN,as does point2.

Initial same-source visual comparison:derived page2 and prior Word ProtectedView/
GDI page2 inspected side by side. Tables,snow-profile drawing and visible numeric
rows remain present. WARNING:side stamp text orientation/line layout differs
(Word rotated side labels versus vertically wrapped labels in derivedPDF).
Line spacing/table placement also differs;source symbol boxes were already
visible in Word reference. Do not reconstruct them or claim pixel/font/symbol
equivalence from this check. Remaining pages/critical objects still require
source-bound comparison. This is not a full content PASS.

Full post-integration Python suite started with consistent UTF8;completion
remains pending in full-suite-render-integrated.log.

## Real-source cell comparison and literal private-use signs

Full post-render integration regression:1343tests/390.637s/OK,34skipped.
This run predates the small private-use-warning addition described below.

Same-source page2 reviewed ROI excludes outer stamp/frame;three tables found
with7x8,4x8,14x3 declared PDF grids. Compared116 logical Word-reference cells
by table/row/column,retaining merged-cell slots rather than global text search.
113 literal text MATCH;3UNRESOLVED:one diagram cell(Word text slash vs noPDF
text),private-use sign label,and label containing private-use code plus subscript
layout. All checked numeric cells match without numeric repair. Receipt records
source/PDF/Word-reference hashes,table bboxes and everycell. Normalization removes
Word cell terminator and collapses whitespace runs only;no guessed symbols.
Evidence:page2-table-comparison.json. Not whole-document/table acceptance.

XML investigation binds side-stamp labels to header1.xml wps:bodyPr vert270.
Specific code points F061/F067/F020 occur literally in w:t;no explicit run-font
or paragraph-style reference at those runs(inherited font not resolved here).
They must not be silently read as standard Greek letters. Office reader now
retains bytes/text and adds PRIVATE_USE_GLYPH_UNVERIFIED for Unicode categoryCo,
including supplementary planes.2TDD tests RED->GREEN;relatedOffice51tests/
13.460s/OK. Independent review:no important findings. Actual source units now
flagged,source SHA unchanged;private-use-glyph-source-check.json.

Broader real Office batch running sequentially in existing queue. Legacy report
DOC conversion failed while original remained unchanged;precise cause is not
proven by generic Worker error. It is not called corrupt or unsupported merely
from failure. Remaining batch continues;do not restart its live process.

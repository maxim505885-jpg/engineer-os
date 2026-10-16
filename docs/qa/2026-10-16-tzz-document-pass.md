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

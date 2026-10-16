# Completion on newly supplied engineering source set

> **For agentic workers:** Use executing-plans inline. Preserve existing implementation and evidence gates.

**Goal:** Close verified document functionality first,then remaining application criteria,using only the user-supplied new engineering inputs.
**Architecture:** Existing engineering layer,authenticated local_app,queue and SPU shell remain. Source hash/versions bound to all new results. No historical evidence substitution,no duplicate runtime.
**Source root:**C:\Users\maxim\Desktop\тззззззз

## Work packages and checks

1. Document qualification:T03/T04. Private native/PDF/ProtectedView/GDI reference
   capture and cell comparison. Compare critical cells/formulas/graphics and
   cross-format revisions,identify controlling task without inventing one.
   Implement only a qualified production source-view path;otherwise record exact
   unavailable boundary. Tests in existing office/document_qualification/source
   assets suites plus actual new source receipts. No blanket PASS from page counts.
2. Engineering source integration:T06/T07/T08/T09/V01. Existing core forms/workers
   on new sources;preserve SPR/DOC/DWG originals and unsupported semantics. Add
   bounded missing functionality with RED->GREEN regressions. Normative comparisons
   require exact full source/edition/clause and actual facts from this source root.
3. Real case/report:T10/T11. Trace every finding to source/revision;validate against
   applicable task. Do not issue responsible-engineer identity or unsupported
   acceptance. Draft DOCX/PDF exports must be rendered and inspected.
4. Desktop release:T01/T02/T12/T13. Reproducible packaged source/runtime manifest,
   current runtime qualification,offline launch,backup/restore/update/rollback,
   ownership and data safety checks. Existing supplied installer remains distinct.
5. Final integration:focused checks,existing Windows/browser suites,independent
   code review for new product code,architecture/repository guards. Record every
   unresolved criterion explicitly;100% only when every applicable check passes.

Current evidence/receipts are private under .engineer-os/tzz-stage2;source data,
private reports and personal identifiers must not be committed. Written QA and
reproducible application changes belong in Git. Original SPU and main user checkout
are preserved. A named environment limitation is not an excuse to stop independent
work;continue unaffected packages and do not fabricate a release or engineering PASS.

### Controlled-render implementation continuation

- Completed:offline owned DOCX feasibility,fw_cfg source identity,representative
  host file/network controls,owned timeout cleanup,host output decoder with RED/
  GREEN and independent review. These are partial gates,not closure ofT03/T04.
- Next:place reusable Windows process/ACL/JobObject mechanics in existing runtime
  bridge,not engineering methodology. Minimal configured command/image allowlist,
  immutable runtime manifest,per-job staging/read-only inputs,noNIC/nohostshares,
  bounded serial output and cancellation. No old experimental DLL dependency.
- Then:package/font inventory and active-content controls;connect derived PDF
  source view to existing application with unverified lineage;test actual new
  corpus,revisions and critical objects against Word/PDF reference evidence.


### Large Office input transport and result

The v3 receipt `office-failure-retry-phases-v3.json` records the 16,372,736-byte
report failing after 300 seconds in the guest controller; the earlier live phase
trace had `INPUT_READ_BEGIN` but no `INPUT_READ_COMPLETE`. This did not establish
document corruption. The suspected fw_cfg performance problem is consistent with
the Linux reader implementation, which reselects the blob and skips preceding
bytes for each read; this is a diagnosis, not a claim about the exact guest kernel
build.

The host now builds a fixed-format raw input disk from the checked staged source:
512-byte header, bounded length, expected SHA-256, exact source bytes and zero
sector padding. QEMU attaches it read-only as a second virtio disk, with no
filesystem or host-directory sharing. The guest opens only `/dev/vdb`, requires a
block device, validates the complete header/padding and SHA-256, then applies the
existing source-format validation before conversion. The small request remains in
fw_cfg. Focused transport/guest/host/queue suite and adjacent Office protocol/bundle
suite: 48 tests PASS. Private v4 bundle
manifest: `00887e47f7bf8715fc9a8128de0f35ad8966bb2d2bfd0411d89aeb519e28e86b`;
v1–v3 bundles remain preserved.

Actual source `Отчет/Ростов ТрансКонтейнер.doc` from the controlling folder rendered
successfully through the v4 guest in 143.614 seconds. Source SHA-256
`5a599aa80e5de542892a085072d02e890de83f65d36ab700af44aad03324c805` remained
unchanged. Derived PDF SHA-256 `7356320f82d1569c81b783dedbc20973b5971b05eb9bfe6af01673f503773604`,
8,831,496 bytes, 68 pages; process exited 0. This establishes conversion-path
functionality for this file only. The matching supplied PDF in the same source
folder is SHA-256 `19f294e9468ea759e8835fa4bae3c109da756f398b03a951e6993329a9cba09f`
and has 65 pages. Direct page-index normalized-text comparison is low, with mean
similarity 0.3026; it is not a fidelity qualification. PDF structure, page/layout,
font, formula, table and image equivalence remain UNVERIFIED; the result remains
`DERIVED_UNVERIFIED` / `UNCERTAINTY`, not evidence or engineering acceptance.

Next: investigate page correspondence and visual/object differences against the
supplied PDF and native source; qualify or explicitly block this renderer for the
source class; then proceed with the remaining corpus and T06/T07/T08/T09/V01
checks. Do not change the production renderer configuration or claim stage 2
closed based on the successful conversion alone.

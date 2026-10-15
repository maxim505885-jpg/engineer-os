# Engineering jobs in the local application

The existing SQLite queue and Worker execute `ENGINEERING_RUN`; no second runtime
or queue is introduced. `/api/sessions/<id>/engineering-runs` exposes the tool
catalog/context revision and accepts an authenticated explicit enqueue request.
The existing generic chat endpoint cannot create an unbound engineering job.

An immutable bounded JSON input record is inserted in the same transaction as
the job. Its digest binds tool/options, input file IDs/hashes and the current
files/Evidence/requirements/domain context. Cross-session files, stale revisions,
nonfinite JSON, server-owned acceptance/source fields and altered request records
are refused. Original hashes are checked before and after calculation. Cancellation
retains the input and any completed progress receipt; retry creates a new attempt.

Supported calculations are the existing simply supported UDL beam, linear XY
nodal-load frame/axial truss and solid rectangular section. All manually entered
numbers are ASSUMED. A file link does not establish that its interpretation or
measurement was verified. Results are CALCULATED candidates. No accepted Evidence,
normative PASS, actual-structure verification or FINAL_AUDIT is created.

The domain panel contains the calculation form before the normative forms. Beam
and rectangle have labeled SI inputs and conditional diagrams; planar input is
an explicit engineering JSON document with nodes/members/loads/kind/units. The
chat shows the main numeric results; a collapsed receipt preserves complete
inputs/results, digests, assumptions and limits. The normal source upload/history
and project selection are reused.

Beam/frame/truss solve in a disposable process. Windows requires pywin32 Job
Objects: the child is created suspended, attached before resume, limited to two
active processes (venv launcher plus interpreter), 2 GiB total/per-process memory,
120 seconds wall time and 2 MiB output. Closing the job kills its owned process
tree. Linux applies RLIMIT_AS/RLIMIT_CPU before solver imports. Missing boundary
support fails closed; this is not network isolation or an Office sandbox.
Rectangle arithmetic is constant-size and executes directly.

Database schema 2 adds `engineering_inputs`. Upgrading a version-0/1 database first
makes and verifies its version-specific SQLite recovery copy. Previous schema-1
applications reject schema 2, preventing an older worker from treating a new
pending engineering job as chat. Backup/restore accepts both old versions and
schema 2 and preserves input records and original IDs. Restore is always into a
new directory. User-owned data/server8765 are not migrated during development.

CAD/IFC inventory/diff adapter code is present but not enabled by this package;
DWG conversion, annotations, IFC geometry/requirements and GUID Evidence still
need their own bounded worker/source review qualifications (T08/T09). Catalog
entries explicitly show that boundary. The whole six-stage plan is not complete.

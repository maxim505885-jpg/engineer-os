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

The negative memory probe commits and touches a fixed 64 MiB allocation, paired
with a positive run at the normal limit and refusal at 16 MiB. Merely importing
IFC/Pynite is not a reliable negative workload: Windows limits committed memory,
as specified by [JOBOBJECT_EXTENDED_LIMIT_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information).
The fixed diagnostic is not exposed through the engineering tool API.

Database schema 2 adds `engineering_inputs`; schema 3 adds the responsible-review
journal. Upgrading an older supported database first
makes and verifies its version-specific SQLite recovery copy. Previous schema-1
applications reject schema 2, preventing an older worker from treating a new
pending engineering job as chat. Backup/restore accepts both old versions and
schemas 2/3 and preserves input records and original IDs. Restore is always into a
new directory. User-owned data/server8765 are not migrated during development.

IFC inventory now runs through the same disposable resource boundary. Upload
preserves the original without parsing it; explicit execution stages a hashed
copy up to 50 MiB. Hash reads and copies are bounded even if a source grows
during reading. Source hashes are rechecked after the child. Native parsing
starts only after the Windows Job/RLIMIT boundary is applied. Declared elements,
storeys, properties and GUIDs remain PROJECT; no accepted Evidence is created.
The UI lists at most 200 elements and retains the complete bounded receipt.
The resource boundary does not claim network isolation or hostile-code safety.

IFC geometry/requirements/diff and GUID Evidence are now connected through the
bounded workflow; see [IFC workflows](ifc-workflows.md) for exact scope and
independent reference receipts. CAD adapters, conversion and annotations still
require T08 qualification before enabling their queue entries. The whole
six-stage plan is not complete.

Optional calculation/BIM requirements include the pinned Windows pywin32 worker
dependency. The optional Linux/Windows workflow exercises these workers and
the calculation/IFC/review Chromium scenarios; configured CI is not a CI PASS
until a run on the published exact head actually succeeds.


## CAD read-only queue — 16.10.2026

В существующей ENGINEERING_RUN очереди доступны CAD_INVENTORY и CAD_DIFF.
Требуются один или два разных DXF file IDs того же проекта, неизменный context
revision и options={}. DWG_CONVERT/CAD_ANNOTATE в этой очереди не включены.
Данные DXF имеют класс PROJECT, не MEASURED и не принятый факт.

cad_process проверяет исходный SHA и размер, создаёт собственные снимки DXF,
затем использует общий calculation_process boundary: 2 GiB памяти, 30 секунд,
2 MiB JSON-результата. Одновременно выполняется не более одного CAD child.
Хеши снимков и оригиналов проверяются повторно; отмена, рост файла или смена
источника не дают пригодного результата. Это ограничение ресурсов, не sandbox
с доказанным запретом сети или чтения произвольных локальных файлов.

Существующий GET session/cad/file inventory теперь использует тот же worker
для DXF. Аннотация, экспорт и locator остаются прежними маршрутами; их полная
resource qualification этим пакетом не выполнена. CAD-профиль включает общий
Windows process-adapter; отсутствие границы даёт явный отказ вместо inline parse.

Бюджеты прежние: каждый DXF до20MiB, inventory до50000 объектов во всех блоках;
редактирование сохраняет отдельный более узкий предел. UI показывает первые100
объектов Model отдельно от общего census count и отмечает усечение. При превышении
лимита чтения inventory не сообщает полноту. CAD_DIFF использует существующий
строгий сериализованный DXF comparator: handles, tags, layers, resources и units.
PASS такого сравнения не доказывает визуальную эквивалентность, правильность
инженерной модели или отсутствие потерь при преобразовании DWG.

Новые операции видны в обычной форме расчётов/CAD/IFC; при выборе сравнения
появляется второй исходник. Результат содержит changed/missing/added handles,
полную квитанцию и ограничения. Evidence и acceptance автоматически не создаются.

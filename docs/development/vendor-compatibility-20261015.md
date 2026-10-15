# Current result: all nine native models — 15.10.2026

This section supersedes the earlier one-model observation below. All nine current
LIR originals opened in installed LIRA2024.2.3.0 through private copies. Each
exported31 default input tables (279 total). Independent validation confirmed
all table hashes, ZIP CRC, exact ZIP/directory bytes, unchanged source and staged
bytes. Geometry observations range37,082–119,781 nodes and44,086–127,780 elements;
all nine exports have zero invalid node references. These observations do not
verify physical geometry, materials, loads or structural adequacy.

Each model still has2,989–4,312 KE57 elements whose auxiliary stiffness is not
extracted. Full loads/combinations, units interpretation and model/run/result
binding remain unqualified. Nine separate saved-result probes used copies with
original basenames, one actual node/element and10 request categories each.
All90 requests returned UNAVAILABLE /0x8000FFFF E_UNEXPECTED, zero value rows.
This proves API access failed in this context; it does not prove results absent.
No solver or Save was invoked. All owned documents closed; source preservation
was rechecked. No preexisting vendor process was terminated.

Private receipts: `vendor/batch-export-receipt.json`, `all-nine-validation.json`,
`all-nine-result-probes.json`, `result-*/.../summary.json` beneath ignored
`.engineer-os/eight-pass/`. Full engineering verification remains BLOCK.
Installed commercial vendor tools are optional existing workstation tools,
not new mandatory dependencies or purchases for ENGINEER OS.

## Historical first-model investigation

# Installed LIRA compatibility audit — 2026-10-15

Status: **PARTIAL_MODEL_TABLE_EXPORT for one current LIR; BLOCK for complete
model/result extraction and engineering verification**. Installed LIRA 2024 actually
opened a private copy of one current 2013-header LIR and exported 31 default input
tables. No solver, vendor Save, registry/settings changes or original modifications
were performed. Vendor UI briefly opened during authorized COM startup.

## Actual installed API

Reused the read-only `LoadTypeLibEx(REGKIND_NONE)` probe from
[PR100](https://github.com/maxim505885-jpg/engineer-os/pull/100), exact head
`2fe90734fa064bf1234827e816c63d4663075204`, file Git blob
`6834fcab11291e02ab29fc0a6a738230c0318434`. Script retained under ignored
`.engineer-os/eight-pass/vendor/api-probe.ps1`; no new binary decoder was built.
The probe executed successfully against installed `Bin/x64` and produced
`ENGINEER_OS_LIRA_API_29e378971c954d84a0e016cb9ad46424/lira-api-inventory.json`
and its ZIP in that ignored directory.

Both embedded type libraries were actually read:

| Installed file | SHA-256 |
| --- | --- |
| LiraSapr.exe, version 2024.2.3.0 | 49b6320e0c3e631c44b33f75b5dfc52343f50019cb6f8914fe009353b71b189a |
| LiraResAPI.dll, version 2024.2.3.0 | b3c18c27fe298c85c8890850390d2c82cc45a5e3c96d22080deec057569ec4df |

`ILiraApplication.OpenDocument(PathName, RestoreEnv, Silent, pMsgs)`,
`ILiraTables`/`ILiraTableGroup.CreateNewItem(Typ, Pars, ModelPart, Nam, AtPos)`
and `ILiraTable.GetContents(pData)` are present. Result-library interfaces include
load-case and combination displacement/force requests, main data, vibration,
fragment/punch loads and selected reinforcement requests. This establishes API
surface availability only, not successful COM invocation, result availability,
model-file compatibility or model/result association.

The registered LocalServer32 for coclass
`b6a075ea-ca19-4011-86b9-6d22f7409c5b` points to installed x64 LiraSapr.exe.
No LiraSapr/LiraFem process was observed in the read-only process snapshot.
Actual ILiraApplication exposes no Visible/Hidden property or Quit/Exit method.
ILiraDocument exposes Close; application-level ownership and hidden startup are
not guaranteed by the inspected API. Hiding a helper console does not hide a
COM server started by Windows. `Silent` is an OpenDocument parameter; its name
does not establish hidden server startup. The authorized bounded run allowed vendor UI startup after a fresh empty vendor
process snapshot; it did not assume that console hiding would hide vendor UI.

## Current user LIR identities

Recursive `Get-ChildItem -Recurse -File -Filter *.LIR` of the current user
calculation folder found **nine files**, three in each section. Exact current
filenames, sizes, timestamps, source SHA-256, bounded header text and before/after
hash checks are in ignored `current-lir-identity.json`. Inventory filenames and
all nine source hashes were unchanged during that run.

Seven files start byte `0x55` (`U`) and have the recognized, null-terminated header
`LIRA-SAPR 2013 software ver.13.0.0.a`. Two section-3 files start `0x24` (`$`),
contain the same readable version text, and continue with binary bytes without
the required null terminator immediately after that text. Existing strict
`inspect_lir` leaves those two declared-format/version fields unknown and reports
`NATIVE_HEADER_UNRECOGNIZED`. This is an unsupported-header observation, not a
claim of corruption. All nine remain native identity observations, without
semantic decoding. The readable 2013 version text is not proof of incompatibility
or compatibility with installed 2024.

A fresh filename snapshot preceded staging one representative smallest source
(section 2, 16,266,163 bytes). Source before/after and staged copy SHA-256 agree:
the exact private `staging-receipt.json` identity.
Ignored `representative-model.lir` and `staging-receipt.json` preserve the copy and
identity. LIRA opened a further private working copy generated by the reused exporter.
All three native byte identities match. Receipt hashes concern native file
identity, never a result file or model/result linkage.

## Existing exporter reuse and remaining work

PR100's exporter v3 already uses a private copy, RestoreEnv=0, Silent=1, default
whole-model tables 2–32 and explicit by-reference VARIANT marshalling; it avoids
SetContents/Apply/Save and solver/result methods. Its README explicitly states
LIRA may open automatically, so its existence does not satisfy hidden startup.
The current run used its reviewed module and bridge, not historical success as
evidence. A wrapper activated COM only after checking no vendor process existed,
used the staged representative only, and imposed a 120-second wall timeout,
128-MiB-per-table and 512-MiB-total TSV monitoring bounds. Bounds are monitored
while exporting rather than allocator hard caps. The module uses RestoreEnv=0,
Silent=1 and closes its owned document in finally.

Actual run 09:26:47.606Z–09:27:06.182Z completed in about 18.6 seconds. Helper PID
42756 started new x64 LiraSapr PID 22144 at 09:26:48.551Z, exact installed path,
with a nonzero window handle. No preexisting vendor process was present. The
owned document closed successfully; only this demonstrably new vendor PID was
terminated afterwards, and a fresh snapshot found no LiraSapr/LiraFem/LirAnSvr2024.
Helper exit-code capture was unavailable (null); success is based on the actual
manifest/TSVs and independent content validation, not that process field.

Actual source/copy-bound export:

- 31/31 default model tables exported; 8,762,187 TSV bytes.
- 37,083 nodes; 44,086 elements; zero invalid node references.
- Element types: 10=4,594; 44=29,419; 42=6,758; 57=3,315.
- 22 ordinary stiffness records; ordinary reference inventory has no missing IDs.
- 16 load-case names; load records and full combinations not established.
- KE57 auxiliary stiffness remains unextracted for 3,315 elements.
- GetParameters unavailable for table types 2,3,8,22,23; six default tables empty
  (7,8,20,21,23,26), which is not proof of absent model content.
- All TSV hashes checked by existing native_tables reader; ZIP CRC, exact member
  list and bytes match the exported directory. ZIP SHA-256:
  the exact private `validation-receipt.json` identity.

This establishes partial semantic compatibility of **this one exact source** with
installed 2024.2.3.0, including usable geometry/connectivity and ordinary stiffness
inventory. It does not establish all nine-file compatibility. Exact unit codes
and their vendor enums are retained, without assuming unit meaning from code
numbers. Geometry/material/support details still require engineering review.

Receipts: ignored `export-result.json`, `bounded-run-receipt.json`,
`native-observation.json`, `validation-receipt.json`, and
`ENGINEER_OS_LIRA_EXPORT_0b58ecf4ed244aeba5e9ee782645cd0b/manifest.json` plus ZIP.
Existing reader correctly leaves its intrinsic original-source binding claim
unverified; the separate run/staging/working-copy hash receipts independently
establish this run's native source-to-copy identity.

[PR102](https://github.com/maxim505885-jpg/engineer-os/pull/102), inspected head
`b623bc3abd58adbf46432fbc4e3adb96d647235c`, contains the existing bounded saved-result
exporter and states no real RES runtime output had been received. Its fixtures
and interface presence do not establish current saved results or run linkage.

**Complete engineering verification remains BLOCK.** Missing verified sections
include auxiliary KE57 stiffness, full original loads/combinations, full
materials/sections and supports/releases semantics, soil interaction, solver
warnings/results and model/result/run correspondence. The other eight current
sources were not opened. No normative verification or acceptance is granted.
Next action is source-bound export and review of remaining input scopes and
models, then saved results with independent model/run binding; do not run the
solver merely to manufacture completion. No calculation execution or FINAL_AUDIT
acceptance is claimed.

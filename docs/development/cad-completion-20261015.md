# Additional native CAD investigation — 15.10.2026

Installed AutoCAD2026 Core Console was also run against a private graphics DWG
copy with an isolated profile; originals were unchanged. A census attempt timed
out after60seconds and remains incomplete. A separate DXFOUT attempt exited0
in about5seconds and wrote27,170,234bytes. Independent ezdxf validation still
failed with missing ENDSEC. Thus native export did not resolve the ODA truncation;
exit0 alone is not export qualification. Internal cause remains UNKNOWN.
Production intake budgets were not raised and no original repair was attempted.
Private `cad/native-graphics*/receipt.json`, logs and `validation.json` preserve
the distinct attempts. AutoCAD remains optional installed vendor software,
not an ENGINEER OS runtime requirement. CAD acceptance remains BLOCK.

## Earlier ODA investigation

# CAD completion evidence — 2026-10-15

Optional engineering adapter: `engineering.cad.conversion.convert_dwg` requires an explicit installed ODA executable and source SHA-256. It reserves a new destination, copies the original into an isolated input directory, runs only that copy with recursion=0/audit=0, records converter identity, command, logs, output identity and source post-check. No installer, settings change, external service, CLI/UI integration or engineering acceptance is added. Existing CAD APIs and safety limits are preserved.

The ledger is source-bound. Independent DWG entity/resource/geometry census is absent, so every conversion remains BLOCK for DWG equivalence. Converter returncode zero and empty logs cannot prove no loss. Derived DXF inventory limitations and diagnostics are retained. Oversized generated DXFs now produce a persisted BLOCK ledger rather than an uncaught intake exception (regression reproduced before the fix).

Actual current source files were located with `Get-ChildItem -Recurse -Force`; default discovery omitted them because of hidden/ignore behavior. Both originals under the supplied folder were copied read-only, converted by installed ODA 27.1.0 to ACAD2018 DXF, and checked unchanged by SHA-256. Both converter exit codes were zero, stdout/stderr empty:

| Original | Original bytes | Derivative bytes | Source SHA-256 |
|---|---:|---:|---|
| Геодезические измерения 03.09..dwg | 10,584,074 | 98,618,017 | private receipt |
| Графика 03.09.2026.dwg | 8,041,370 | 27,113,019 | private receipt |

Both generated DXFs exceed the existing 20 MiB intake limit. Conversion verification therefore remains BLOCK. Private evidence: `.engineer-os/eight-pass/cad/actual-summary.json`, `actual-rerun-{0,1}/conversion.json`, staged copies, output DXFs and logs. The preliminary `actual-0` attempt exposed the oversized-output exception; it is retained as failed-attempt evidence and is superseded by the named rerun.

An explicit one-off ezdxf derivative census/export run is stored separately in `derivative-census-and-export.json`; it is not an independent DWG source census. Existing strict `compare_dxf` is attempted and blocks under unchanged intake limits. No accepted roundtrip or lossless DWG claim follows.

Validation: RED missing adapter test, GREEN adapter suite; RED oversized-output reproduction, GREEN regression. `python -m unittest tests.test_cad_conversion_route tests.test_cad_roundtrip_comparison tests.test_cad_workflow -q`: 29 tests, OK. Seven new route tests cover isolation/audit flags, diagnostics and permanent equivalence block, failed or missing output, identity mismatch before execution, existing destination protection, timeout, oversized derivative, and zero-exit truncated ASCII output.

Historical p14 source refers to a different building. Its earlier LibreDWG warning/count claims are not evidence for the current sources and have not been promoted into this ledger. An independent native DWG census, source-versus-export resource/geometry checks, and visual engineering review are still required. Current result: BLOCK; no FINAL_AUDIT acceptance.

Actual derivative investigation: geodesy DXF was parsed explicitly outside the production adapter for evidence gathering: 218,304 entities, 67 layers, 4,527 blocks, units=4, including 445 ACAD_PROXY_ENTITY. This exceeds the unchanged 50,000 inventory-entity budget as well as the 20 MiB byte cap. A separate ezdxf export was generated; strict comparison BLOCK remains. These counts describe the converted DXF only.

Graphics DXF failed ezdxf with DXFStructureError: missing ENDSEC tag. Its tail stops at `100 / AcDbBlockReference`, without terminal EOF. A fresh ACAD2018 conversion reproduced exactly 27,113,019 bytes and the same terminal record. Three post-exit observations at two-second intervals had identical SHA-256/size; process inventory showed no remaining ODAFileConverter process. Thus observed failure is reproducible after process exit, rather than an unobserved delayed writer. Converter internals/source geometry cause remains UNKNOWN. `graphics-probes.json` preserves the separate 2018/2013 experiments and stable-file receipts. The new EOF regression now classifies incomplete ASCII derivative output explicitly; original run receipts remain untouched.

No larger production intake budget was enabled: actual geodesy output exceeds both existing byte/entity caps and no bounded-memory/resource-safety qualification has been established. Neither conversion acceptance nor DWG equivalence is established by the one-off census.

ACAD2013 repeat also returned zero with empty stdout/stderr but stopped at the same `AcDbBlockReference` record: 27,122,603 bytes, three identical post-exit hashes, no remaining ODA process, original unchanged. Changing DXF target version did not resolve the truncation. No native repair/audit was enabled, and no repair of user files was attempted.

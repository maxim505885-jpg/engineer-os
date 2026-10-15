# BIM completion evidence — 2026-10-15

Scope: optional local IFC PROJECT mesh bounds and explicit declared-property checks.
Existing `inspect_ifc` / `compare_ifc` APIs are unchanged. No BIM server or paid
service added. No structural solver, actual-condition acceptance or normative
certification is implied.

- `engineering.bim.ifc_geometry.inspect_geometry`: requires SHA-256 source match,
  valid single-project units/GUIDs/container inventory. Runs IfcOpenShell geometry
  in a separate process with a configurable <=60 second timeout, <=1000 target
  elements, <=200000 total returned vertices and bounded JSON. World-coordinate
  bounds are expressed in metres (IfcOpenShell default SI conversion); input
  project scale is retained. Each row includes GUID locator and source SHA-256.
  Missing representation is NOT_VISIBLE / NOT_VERIFIED. Failed geometry remains
  NOT_VERIFIED, never an absent-defect conclusion. Geometry kernel allocation is
  not hard-memory-capped: vertex bounds are checked after triangulation. Treat
  untrusted hostile IFC in a separate OS resource-restricted environment.
- `engineering.bim.ifc_requirements.check_requirements`: strict JSON-style contract
  with unique requirement id, user source, supported IFC type, property set,
  property, exact scalar expectation and declared unit semantics. This is a
  deliberately narrow local contract, not an IDS/IfcTester implementation.
  Numeric length checks require one actual IfcQuantityLength with inherited
  project unit; explicit per-quantity units remain unverified. Missing values,
  no targets and unverified length units produce UNCERTAINTY. An explicit scalar
  mismatch is ERROR only for that supplied requirement. Overall remains
  UNCERTAINTY with acceptance/calculation verification false.

Verification: TDD initial new API tests failed with missing modules; unit-confusion
negative test failed PASS vs UNCERTAINTY, then corrected actual quantity-type gate.
`.venv-engineering/Scripts/python.exe -m unittest tests.test_ifc_geometry_completion tests.test_ifc_adapter -q`
PASS: 24 tests, including existing adapter regressions, synthetic extruded wall
6 m world bound from millimetre project, missing representation, source mismatch,
invalid limits, timeout, incorrect worker provenance and area disguised as length.
Synthetic geometry is generated in a temporary test directory, never presented
as user model evidence. Source files are read-only.

Actual IFC: recursive `Get-ChildItem -Recurse -Filter *.ifc` of
`C:/Users/maxim/Desktop/ДЛЯ ИИ` returned none. Actual-model validation remains
BLOCK pending a user IFC and controlling geometry/property requirements.
No model equivalence, solid validity, volume, clash, calculation or ACCEPTED claim.


Review corrections: inverse unit disguise (length labelled unitless) reproduced red
then fixed. All scalar checks now inspect native IFC property/quantity type.
Dimensionless checks require supported count/ratio/real/integer types with no
explicit unit; unknown dimensions remain UNCERTAINTY. Worker JSON now rejects
NaN/Infinity, wrong row keys/type/unit/status, reversed/nonfinite bounds, and
invalid/over-limit vertex counts; unverified rows require null bounds. Final 24
BIM tests PASS, including genuine unitless real property and explicit-unit veto.

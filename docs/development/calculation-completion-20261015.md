# Calculation controls — 2026-10-15

Implemented optional Python APIs in `engineering/calculation/planar_control.py` and
`section_control.py`. They are not wired into acceptance, CLI, or source import.

## Supported scope

`PlanarInput`: typed immutable XY nodes, straight prismatic members with individual
E, A, Iz; explicit translational/rotational support booleans; global FX/FY/MZ nodal
loads; one unit-factor load combination; linear elastic small-displacement analysis.
`kind="frame"` uses rigid member joints. `kind="truss"` releases both in-plane member
end rotations, restrains inactive nodal RZ, and rejects applied moments. Out-of-plane
DOFs are restrained. Auxiliary G, nu, Iy, J are numerical constants inactive in this
scope, not actual material data. No arbitrary releases, distributed loads, self weight,
shear deformation, P-delta, buckling, plasticity, dynamic analysis, normative strength
checks, or 3D/plate/shell behavior are offered. Truss Iz is a required positive numerical
section input although released bending is inactive. Maximum 500 nodes/1000 members.

`RectangleInput`: solid rectangle area, centroid, centroidal Iy/Iz and elastic section
moduli only. Width follows section z; height follows section y. No holes, composites,
rolled profiles, torsion constant, warping, or strength/acceptance evaluation.

Both APIs require explicit `N_m_Pa`, a lowercase SHA256 source reference and unique
nonblank evidence IDs; retain input data, provenance references and deterministic input
SHA256 on calculation. References are caller assertions, not independently verified
source bytes. A calling ingestion layer must validate their correspondence to evidence.
PASS means successful scoped numerical calculation plus finite-result and global force/
moment equilibrium checks (planar API), not verification of an actual structure or
engineering acceptance. Solver exceptions/instability return BLOCK. Normative
verification is always NOT_RUN, acceptance_granted and actual_structure_verified false.

## Verification evidence

TDD red: tests initially failed on missing new modules. Implemented and verified using
existing `.venv-engineering/Scripts/python.exe`, PyniteFEA 3.2.0. Final command:

```
.venv-engineering/Scripts/python.exe -m unittest tests.test_planar_control tests.test_section_control tests.test_control_beam
```

23 tests PASS, 0 failures/errors (2026-10-15). Includes horizontal and vertical
cantilever PL^3/(3EI), multi-member rigid elbow Castigliano displacement including
column axial shortening, axial bar PL/EA, triangular truss virtual-work displacement,
rectangular area/inertia/modulus identities; support instability; invalid connectivity,
zero length, negative/nonfinite properties/loads, wrong units, missing/duplicate
provenance, bool numeric values, solver nonfinite output, deterministic source binding; separate per-axis force and moment tolerance scales with a corrupt-reaction/large-moment regression.
All benchmark data are SYNTHETIC; none are actual measured/project inputs.

Current actual-input folder scan is owned by the main audit. It now contains the
`Расчёты` tree with three calculation sections and LIR files/backups; this code does
not read, mutate, import, convert, or solve those proprietary source files. There is
no claimed LIRA/SCAD format compatibility and no actual-source calculation result.

## Remaining qualification

Independent broad numerical qualification and engineer-controlled mapping from source
model assumptions, geometry, sections, materials, combinations and restraints remain
necessary before any project-specific use. Analytical unit tests qualify the narrow
implemented paths only. No structural compliance, safety, defect or acceptance claim
is made. No source originals or paid services were used or modified.

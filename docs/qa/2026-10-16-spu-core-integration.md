# SPU interface and desktop integration — 2026-10-16

## Delivered scope

Separate working adaptation of the supplied SPU interface and Electron application
connected to the existing ENGINEER OS backend. Baseline commit:4e4c46f.
The original SPU and immutable17-file import are unchanged: repeated SHA256 checks
of all17 source and copied files found zero mismatches.

| Entry point | Existing core used |
|---|---|
| Projects/dashboard | Sessions, current snapshot, files/jobs, fresh final audit |
| Documents and technical assignment | Original uploads, extraction, requirements and source preview |
| Source review | Evidence register, source confirmation and responsible verification |
| Norms/calculations/CAD | Existing domain packets, normative catalog, bounded calculation/IFC/CAD workers |
| Project conclusion | Existing case snapshot, FINAL AUDIT, draft versions and DOCX/PDF exports |
| Tasks/results | Durable queue, job history, cancellation/retry |
| Knowledge | Existing CAD annotations/memory and mandatory reverification |
| Model settings/chat | Existing model configuration and CHAT/CORE workflows |

SPU layout, palette, hero photograph, icons, splash, window/tray/state code are
reused. Existing controllers/forms are retained; loaded-state events populate the
new dashboard without extra bootstrap API requests. Source SPU Flask/server.py,
platform.db and historical acceptance are not imported.

## Verification

- Full pinned native Windows Python suite:1310tests,434.139s,34skipped,OK.
  Private raw log:`.superpowers/sdd/2026-10-16-spu-interface-desktop/full-suite.log`.
- Focused Python desktop/build identity:11tests,OK after final lifecycle changes.
- Node desktop boundary:6/6PASS. Exact main-frame IPC, canonical loopback startup,
  output limits, external schemes, foreign build rejection, actual delayed Python
  cancellation with child PID gone. Cancellation test was RED before the fix.
- Actual supplied Electron33.4.11:PASS. Real page,16existing forms,loaded workspace,
  isolated data/state,context bridge,Node unavailable in renderer,icons/window-state,
  screenshot and owned backend stopped. Report under
  `.engineer-os/spu-desktop-qualification/state/self-test-result.json`.
- Chromium shell:PASS, empty/populated projects, upload/counters,hostile titles,
  session switch,draft preservation,desktop/mobile overflow.
- Chromium normative catalog,CAD worker,IFC inventory/geometry/requirements/diff,
  rectangle/beam/planar calculations,conclusion export,CAD-memory:PASS.
- Independent review found pending-startup child leak (P1). Fixed with abort+await,
  serialized restart and guarded quit; focused reviewer confirmed repair. Reviewer
  test execution was sandbox-blocked and is not counted as independent test PASS.
- Architecture guard,dependency consistency,JavaScript syntax:PASS.

Initial DOM checks exposed missing matchMedia in emulation, fixed by optional
browser-capability fallback. A normative fixture selected the second source before
its option arrived; test now waits for both source options. Windows DOM cleanup now
stops its own Python process tree before deleting the test database. Intermittent
Drive bootstrap and IFC timeouts were preserved; isolated Drive and IFC repeats
passed without weakening assertions. Full DOM final repeat:PASS (12synthetic model requests, all existing assertions retained).
The earlier post-reload status timeout did not reproduce on this final run; its
root cause remains unproven and is retained here rather than declared fixed.
Drive isolated DOM repeat:PASS. Repository guard:PASS (689tracked files);diff check:PASS.

## Remaining release/engineering scope

Launch:`Open_ENGINEER_OS_SPU.cmd` in this checkout. It uses project Python and the
existing supplied Electron runtime, with explicit runtime override available. It
installs nothing and retains ENGINEER OS active-data selection/lock behavior.

This is a qualified local development launch, not a standalone Windows release.
New installer packaging,updated runtime qualification,signing and clean-machine
installation are OPEN. Original SPU1.2.0 installer remains the original product.
No physical-object acceptance,external service connection or solver/model result
is asserted by this UI integration. Deferred point2 remains deferred; prior CAD,
calculation and engineering limitations remain in force.

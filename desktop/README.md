# ENGINEER OS with supplied SPU interface and application

Open `Open_ENGINEER_OS_SPU.cmd` from this checkout. The launcher uses the project's
`.venv-engineering` Python and the existing supplied Electron runtime. An explicit
runtime can be selected with `--electron PATH` or `ENGINEER_OS_ELECTRON_EXE`.
It does not install packages, activate paid services, or modify the supplied SPU.

The window, tray, icons, splash and window-state implementation derive from the
supplied SPU desktop application. The dashboard reuses its layout, palette and
city photograph. Existing ENGINEER OS forms/controllers and authenticated Python
backend provide the functionality. There is no imported SPU Flask backend or database.

The application starts its own backend on an OS-selected loopback port and verifies
its source/data identity against the authenticated build API. Busy data directories
are rejected. Quit cancels pending startup, waits for shutdown, and stops only its
own process tree. Closing the window normally hides it in the tray; choose Exit
from the tray menu to stop the application. This preference is configurable there.
Desktop state is separate from original SPU state. Existing ENGINEER OS active-data
selection rules apply; use `--data-dir PATH` to select a different data directory.

Local qualification:

```powershell
.venv-engineering/Scripts/python.exe scripts/launch_spu_desktop.py --self-test --data-dir .engineer-os/spu-test/data --state-dir .engineer-os/spu-test/state
$env:PYTHON=(Resolve-Path .venv-engineering/Scripts/python.exe).Path
node --test tests/desktop_owner.test.cjs
```

The self-test requires explicit isolated data/state folders, opens the real page,
checks loaded workspace/forms/preload, captures a screenshot and saves
`self-test-result.json` in the specified state directory.

This is a locally tested development application. The supplied Electron33.4.11
was used without downloading a different runtime. A new standalone installer,
current runtime qualification, signing and clean-machine installation remain
separate release work. The immutable imported SPU1.2.0 installer still launches
its original application; it is not the integrated ENGINEER OS installer.
Engineering acceptance, unavailable models and deferred document qualification
retain their existing evidence/status requirements.

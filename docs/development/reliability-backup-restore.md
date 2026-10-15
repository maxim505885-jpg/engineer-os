# ENGINEER OS Reliability / Backup / Restore

Stage: MASTER PLAN №12.

## Scope

This reliability layer protects the local application data directory. It is separate from
`Backup_ENGINEER_OS_REPOSITORY.cmd`, which protects Git history/source code.

Default application data:

`.engineer-os/local-app`

It contains the SQLite state and immutable originals used by:
- conversations/history;
- source files;
- evidence candidates;
- source reviews;
- requirements and assessments;
- domain/normative/calculation packets;
- extraction journals and analysis receipts;
- Stage7 real-case snapshots;
- FINAL AUDIT records.

## Backup

Windows:

`Backup_ENGINEER_OS.cmd`

The application must be closed. If another ENGINEER OS process owns the data directory,
backup returns BLOCK instead of racing active writes.

Default output:

`Documents\ENGINEER_OS_DATA_BACKUPS\engineer-os-data-YYYYMMDD-HHMMSS.zip`

The archive contains:
- consistent SQLite snapshot made with the SQLite backup API;
- all registered original files;
- manifest with SHA256 + size for the database and every original;
- table counts;
- safe non-secret runtime configuration only.

Secrets are intentionally excluded. OAuth tokens, model keys and `.env` files are not
placed in the data backup.

## Validation

`engineering.local_app.backup.validate_backup()` verifies before restore:
- valid ZIP structure;
- no unsafe archive paths;
- exact file set matches manifest;
- database SHA256/size;
- `PRAGMA integrity_check`;
- `PRAGMA foreign_key_check`;
- required ENGINEER OS tables;
- table counts;
- every original SHA256/size;
- database file IDs match manifest.

A mismatch is BLOCK. The target is not modified.

## Restore

Windows:

`Restore_ENGINEER_OS.cmd`

You may drag a backup ZIP onto the CMD file or run it and paste the full path.

Restore is deliberately fail-closed:
- target must be missing or empty;
- existing ENGINEER OS data is never overwritten automatically;
- archive is fully validated first;
- originals are restored into the new data directory;
- absolute `files.path` entries in SQLite are rebound to the restored location;
- database integrity and file identities are checked again;
- restore creates no new acceptance decision and does not upgrade any audit.

For a disaster restore into the normal default data directory, first move the damaged
directory aside for forensic/recovery purposes. Do not delete it until the restored copy
has been checked.

## Migration safety

Before legacy SQLite columns are altered, `Store` creates a snapshot under:

`<data-dir>/pre-migration/history-<timestamp>.sqlite3`

Fresh databases use the current schema directly and do not create unnecessary migration
snapshots.

## Original-file write safety

New originals are written to a unique `.partial-*` file, flushed and fsynced, then
atomically moved into place with `os.replace`.

If the final replace fails, the partial file is removed and no database record is created.

## Crash / stale-lock recovery

`app.lock` is a persistent lock file, but ownership is provided by the operating-system
file lock, not by the mere existence of the file.

Tests prove:
- a second live owner is blocked;
- after a process is forcibly terminated, the stale file does not prevent reacquisition;
- the launcher can restart against the same data directory after forced process exit;
- jobs left RUNNING/ATTACHMENT are converted to FAILED on startup rather than being
  silently treated as successful.

## Browser release gate

The release candidate runs real Playwright Chromium in CI in addition to HTTP/jsdom.
Stage11 reference screenshots remain diagnostic artifacts.

Stage12 does not claim physical Windows runtime verification; that remains MASTER PLAN №9
and is intentionally deferred to the final Windows pass.

## Fail-closed invariants

Backup/restore must never:
- invent evidence;
- change source SHA256;
- change BLOCK/UNCERTAINTY into PASS/ACCEPTED;
- create a FINAL AUDIT;
- make a stale audit fresh;
- overwrite existing data without an explicit separate recovery decision.

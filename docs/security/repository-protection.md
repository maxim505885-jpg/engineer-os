# Repository protection baseline

Status: 07.10.2026.

## Verified repository state

Repository: `maxim505885-jpg/engineer-os`.

Observed:
- owner: `maxim505885-jpg`;
- owner permission: `admin`;
- visibility: `public`;
- default branch: `main`;
- repository rulesets API currently returns an empty list;
- connected managed GitHub App cannot access administrative branch-protection settings.

## Protection now stored in the repository

- `.github/CODEOWNERS`: all files owned by `@maxim505885-jpg`;
- `SECURITY.md`: security reporting and fail-closed invariants;
- `.github/dependabot.yml`: weekly Python/npm/GitHub Actions dependency updates;
- `.github/workflows/repository-security.yml`: secret-path and repository integrity guard;
- `.github/workflows/repository-backup.yml`: scheduled/manual full-history git bundle artifact;
- `scripts/repository_guard.py`: blocks tracked local env/credential files and unresolved merge markers;
- `.github/pull_request_template.md`: engineering/security review checklist;
- `Backup_ENGINEER_OS_REPOSITORY.cmd`: one-click independent local repository backup;
- `scripts/backup_repository.ps1`: fetch + git bundle + SHA256 + bundle verify + project-map copy.

## Administrative settings still required in GitHub Settings

The connected GitHub App does not have access to change these settings. Configure them once in the GitHub UI.

### Main branch protection / ruleset

Target branch: `main`.

Enable:
- require a pull request before merging;
- require approvals;
- require review from Code Owners;
- dismiss stale approvals when new commits are pushed;
- require conversation resolution;
- require status checks before merging;
- block force pushes;
- block branch deletion;
- do not allow bypass except a deliberate emergency owner bypass.

Required checks after the hardening PR is merged:
- `ENGINEER OS Core Tests / core-tests`;
- `Repository Security Guard / repository-guard`.

### Repository security

Enable where GitHub offers the option:
- Dependabot alerts;
- dependency graph;
- secret scanning;
- push protection;
- private vulnerability reporting.

Review:
- Collaborators and teams: only people who truly need write/admin;
- Installed GitHub Apps: remove write/admin access when no longer needed;
- deploy keys and tokens;
- Actions permissions.

### Owner account

Enable and keep:
- two-factor authentication;
- passkey or hardware security key if available;
- recovery codes stored offline;
- no shared password;
- review active sessions and authorized OAuth/GitHub Apps.

## Backup model

The scheduled GitHub artifact helps with accidental branch/history damage, but it is stored inside the same GitHub repository context. It is **not sufficient for complete repository deletion or account loss**.

For independent protection, periodically run:

`Backup_ENGINEER_OS_REPOSITORY.cmd`

Default destination:

`Documents\ENGINEER_OS_BACKUPS\<timestamp>\`

Each backup contains:
- `engineer-os.bundle`;
- SHA256 file;
- `backup.json` with branch/head;
- current `ENGINEER_OS_PROJECT_MAP.md`.

Keep at least one backup outside the GitHub account, ideally on another disk or separately controlled cloud storage.

## Restore from bundle

Example:

```powershell
git clone C:\path\to\engineer-os.bundle engineer-os-restored
cd engineer-os-restored
git branch -a
git log --oneline --all --decorate -n 20
```

Do not overwrite the active checkout until the restored repository has been checked.

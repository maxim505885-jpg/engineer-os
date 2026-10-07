# Repository protection baseline

Status verified: 07.10.2026.

## Repository

`maxim505885-jpg/engineer-os`

Current facts:
- owner: `maxim505885-jpg`;
- owner permission: `admin`;
- visibility: `public`;
- default branch: `main`;
- current hardening baseline merged into `main` at `0bb024b188895b2db7f931afc106ef14b42ca97c`;
- only repository collaborator returned by GitHub: `maxim505885-jpg`;
- deploy keys: none;
- repository webhooks: none;
- open secret-scanning alerts at verification time: none.

## Main branch protection — ACTIVE

Verified GitHub branch protection:
- pull request required before merge;
- protection enforced for administrators;
- force pushes blocked;
- branch deletion blocked;
- linear history required;
- conversations must be resolved;
- required status checks are strict / branch must be current;
- current required check: `repository-guard`;
- approving review count is currently 0 because this is a single-owner personal repository;
- Code Owner approval is not required yet, because the only CODEOWNER is also the sole owner and self-review cannot be used as an independent approval.

During release consolidation, when the current Stage-9/release candidate becomes the basis of `main`, add `core-tests` as a second required status check.

## Repository settings — ACTIVE

Verified:
- auto-merge enabled;
- update-branch enabled;
- merge commits disabled;
- squash merge enabled;
- rebase merge enabled;
- merged head branches auto-delete;
- web commit signoff required;
- secret scanning enabled;
- secret scanning push protection enabled;
- private vulnerability reporting enabled;
- CodeQL default setup enabled for Python and JavaScript/TypeScript;
- CodeQL setup run `37676414879` completed successfully;
- repository description is set.

## Protection stored in Git

The repository contains:
- `.github/CODEOWNERS`;
- `SECURITY.md`;
- `.github/dependabot.yml`;
- `.github/workflows/repository-security.yml`;
- `.github/workflows/repository-backup.yml`;
- `scripts/repository_guard.py`;
- `.github/pull_request_template.md`;
- hardened `.gitignore`;
- `Backup_ENGINEER_OS_REPOSITORY.cmd`;
- `scripts/backup_repository.ps1`.

The Repository Security Guard blocks tracked environment files, OAuth/credential-like paths, common private-key formats and unresolved merge markers.

## Backup model

GitHub Actions creates a scheduled/manual full-history git bundle artifact.

That artifact helps with accidental branch/history damage while the GitHub repository still exists. It is **not independent protection against complete repository deletion or GitHub account loss**.

For independent protection run:

`Backup_ENGINEER_OS_REPOSITORY.cmd`

Default destination:

`Documents\ENGINEER_OS_BACKUPS\<timestamp>\`

Each local backup contains:
- `engineer-os.bundle`;
- bundle SHA256;
- `backup.json` with branch/head;
- current `ENGINEER_OS_PROJECT_MAP.md` when present.

Keep at least one copy outside the GitHub account.

## Restore from a local bundle

Example:

```powershell
git clone C:\path\to\engineer-os.bundle engineer-os-restored
cd engineer-os-restored
git branch -a
git log --oneline --all --decorate -n 20
```

Verify the restored repository before replacing any active checkout.

## One remaining GitHub server-side setting

At the latest verification, GitHub reports:

`dependabot_security_updates.status = disabled`

and the Dependabot alerts REST endpoint returns that Dependabot alerts are disabled.

The connected GitHub admin tools expose Dependabot configuration files and alerts, but not the GitHub server-side toggle that enables vulnerability alerts / automated security fixes for this personal repository.

The configuration file `.github/dependabot.yml` is already on `main`.

Remaining manual GitHub UI action:

**Settings → Security & analysis / Advanced Security → Dependabot alerts → Enable**

and, if shown separately:

**Dependabot security updates → Enable**

After this is enabled, re-run the repository security verification and add Dependabot alerts to the confirmed ACTIVE list above.

## Account-level protection

Repository APIs cannot verify every owner-account security setting. The owner account should keep:
- two-factor authentication enabled;
- passkey or hardware security key where available;
- recovery codes stored offline;
- periodic review of active sessions and authorized OAuth/GitHub Apps;
- no shared password.

These are account controls, not repository files.

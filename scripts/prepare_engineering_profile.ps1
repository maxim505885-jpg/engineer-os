param([string]$Python,[switch]$InventoryOnly)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$RepoRoot=Split-Path -Parent $PSScriptRoot
if(!$Python){$Python=Join-Path $RepoRoot '.venv-engineering\Scripts\python.exe'}
if(!(Test-Path -LiteralPath $Python -PathType Leaf)){throw 'Engineering Python is absent. Prepare an isolated environment from requirements-engineering-windows.lock; this command never downloads packages or models.'}
$Python=(Resolve-Path -LiteralPath $Python).Path
$Receipt=Join-Path $RepoRoot '.engineer-os\profiles\engineering\capability-report.json'
$ProbeArgs=@((Join-Path $PSScriptRoot 'qualify_engineering_profile.py'),'--profile','engineering','--output',$Receipt)
if(!$InventoryOnly){$ProbeArgs+='--probe'}
& $Python @ProbeArgs
if($LASTEXITCODE-ne 0){throw 'Engineering profile probe failed; no readiness claim was issued.'}
Write-Host 'Diagnostic receipt only. Missing capabilities remain explicit; base chat can start. No packages or models downloaded.'

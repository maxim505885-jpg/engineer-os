param([string]$ECCCheckout = "")
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$probe = Join-Path $project 'experiments\ecc-memory\check_adapter_cli.py'
$report = Join-Path $project '.engineer-os\ecc-memory-windows-check.json'
$pin = 'ef648e01899ba3e8dc6371642deaaf64b4477775'
if (!(Test-Path -LiteralPath $probe)) { throw "Probe missing: $probe" }
if (!(Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js not found. Install Node.js from https://nodejs.org/en/download/ and reopen PowerShell.' }
if (!(Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git not found. Install Git from https://git-scm.com/downloads/win and reopen PowerShell.' }
$python = Join-Path $project '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) { throw "Project Python not found: $python" }
if (!$ECCCheckout) { $ECCCheckout = [IO.Path]::GetFullPath((Join-Path $project '..\engineer-os-ecc-runtime')) }
if (!(Test-Path -LiteralPath $ECCCheckout)) {
    & git clone --filter=blob:none --no-checkout https://github.com/affaan-m/ECC.git $ECCCheckout
    if ($LASTEXITCODE -ne 0) { throw 'ECC download failed; existing project files were not changed.' }
    & git -C $ECCCheckout checkout --detach $pin
    if ($LASTEXITCODE -ne 0) { throw 'Pinned ECC checkout failed.' }
}
# Never switch or reset an existing checkout: the Python transport checks it.
New-Item -ItemType Directory -Path (Split-Path -Parent $report) -Force | Out-Null
& $python $probe $ECCCheckout $report
if ($LASTEXITCODE -ne 0) { throw 'ECC memory smoke check failed. Do not enable working memory.' }
Write-Host "REPORT: $report"
Write-Host 'Synthetic smoke check complete. Working memory is not enabled.'

# Optional OfficeCLI for DOCX/XLSX/PPTX review. No PATH, profile, or MCP changes.
# This installs a tool, not an engineering verification provider.
$ErrorActionPreference = 'Stop'
if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
    throw 'This pinned package supports Windows x64 only.'
}
$repoRoot = Split-Path -Parent $PSScriptRoot
$toolDir = Join-Path $repoRoot '.engineer-os/tools/officecli'
$destination = Join-Path $toolDir 'officecli.exe'
$expected = '05dd712595690672ea1c220a516c0996a27f7c3e7f870a270c19d538e9fc04f3'
$url = 'https://github.com/iOfficeAI/OfficeCLI/releases/download/v1.0.153/officecli-win-x64.exe'
New-Item -ItemType Directory -Force -Path $toolDir | Out-Null
if (Test-Path $destination) {
    if ((Get-FileHash -Algorithm SHA256 $destination).Hash.ToLowerInvariant() -ne $expected) {
        throw 'Existing OfficeCLI checksum differs; inspect it before replacing.'
    }
    Write-Output $destination
    exit 0
}
$temporary = Join-Path $toolDir ([Guid]::NewGuid().ToString() + '.download')
try {
    Invoke-WebRequest -Uri $url -OutFile $temporary
    if ((Get-FileHash -Algorithm SHA256 $temporary).Hash.ToLowerInvariant() -ne $expected) {
        throw 'Downloaded OfficeCLI checksum mismatch.'
    }
    Move-Item -Path $temporary -Destination $destination
    Write-Output $destination
} finally {
    if (Test-Path $temporary) { Remove-Item $temporary }
}

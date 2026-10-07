param(
  [string]$Destination = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'ENGINEER_OS_BACKUPS')
)
$ErrorActionPreference='Stop'
$RepoRoot=Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if(-not (Get-Command git -ErrorAction SilentlyContinue)){throw 'git is not available in PATH'}
if(-not (Test-Path (Join-Path $RepoRoot '.git'))){throw 'Run this from a real ENGINEER OS git checkout'}

$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$target=Join-Path $Destination $stamp
New-Item -ItemType Directory -Force -Path $target|Out-Null

Write-Host 'Fetching current remote refs...'
git fetch --all --prune --tags
if($LASTEXITCODE-ne 0){throw 'git fetch failed'}

$bundle=Join-Path $target 'engineer-os.bundle'
Write-Host "Creating bundle: $bundle"
git bundle create $bundle --all
if($LASTEXITCODE-ne 0){throw 'git bundle create failed'}

git bundle verify $bundle
if($LASTEXITCODE-ne 0){throw 'git bundle verification failed'}

$hash=(Get-FileHash -Algorithm SHA256 $bundle).Hash.ToLowerInvariant()
Set-Content -Encoding ASCII -Path (Join-Path $target 'engineer-os.bundle.sha256') -Value "$hash  engineer-os.bundle"

$map=Join-Path $RepoRoot 'ENGINEER_OS_PROJECT_MAP.md'
if(Test-Path $map){Copy-Item $map (Join-Path $target 'ENGINEER_OS_PROJECT_MAP.md')}

$meta=[ordered]@{
  created_at=(Get-Date).ToString('o')
  repository=$RepoRoot
  head=(git rev-parse HEAD).Trim()
  branch=(git branch --show-current).Trim()
  bundle_sha256=$hash
}
$meta|ConvertTo-Json|Set-Content -Encoding UTF8 (Join-Path $target 'backup.json')

Write-Host ''
Write-Host 'ENGINEER OS REPOSITORY BACKUP READY' -ForegroundColor Green
Write-Host $target

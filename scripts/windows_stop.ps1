$ErrorActionPreference='SilentlyContinue'
$RepoRoot=Split-Path -Parent $PSScriptRoot
$items=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8765 -State Listen
foreach($c in $items){
  $p=Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
  if($p -and $p.ProcessName -match 'python'){Stop-Process -Id $p.Id -Force}
}
Write-Host 'ENGINEER OS stopped. Ollama/Open WebUI left running for fast reuse.'

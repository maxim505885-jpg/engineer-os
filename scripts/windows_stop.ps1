$ErrorActionPreference='SilentlyContinue'
$uri='http://127.0.0.1:8765'
try {
  $response=Invoke-WebRequest -UseBasicParsing -Uri $uri -TimeoutSec 2 -MaximumRedirection 0
  if($response.StatusCode -ne 200 -or $response.Content -notmatch 'ENGINEER OS'){
    Write-Host 'Port 8765 is not ENGINEER OS; nothing stopped.'
    exit 2
  }
} catch {
  Write-Host 'ENGINEER OS is not running.'
  exit 0
}
$items=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8765 -State Listen
foreach($c in $items){
  $p=Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
  if($p -and $p.ProcessName -match 'python'){Stop-Process -Id $p.Id -Force}
}
Write-Host 'ENGINEER OS stopped. Ollama/Open WebUI left running for fast reuse.'

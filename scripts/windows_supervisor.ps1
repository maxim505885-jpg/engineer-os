param([switch]$NoBrowser,[switch]$SkipOpenWebUI,[switch]$ForceDependencyCheck)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)

$RepoRoot=Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$RuntimeDir=Join-Path $RepoRoot '.engineer-os\runtime\windows'
$LogDir=Join-Path $RepoRoot '.engineer-os\logs'
$VenvPython=Join-Path $RepoRoot '.venv\Scripts\python.exe'
$AppUrl='http://127.0.0.1:8765'
$OllamaUrl='http://127.0.0.1:11434'
$OpenWebUIUrl='http://127.0.0.1:8080'
$Model=if($env:ENGINEER_OS_LOCAL_MODEL){$env:ENGINEER_OS_LOCAL_MODEL}else{'qwen3:8b'}
New-Item -ItemType Directory -Force -Path $RuntimeDir,$LogDir|Out-Null
$SupervisorLog=Join-Path $LogDir 'windows-supervisor.log'

function Log([string]$m){$line=('{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$m);Write-Host $line;Add-Content -Encoding UTF8 -Path $SupervisorLog -Value $line}
function Test-Http([string]$u,[int]$t=2){try{$r=Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec $t -MaximumRedirection 0;return $r.StatusCode -ge 200 -and $r.StatusCode -lt 500}catch{return $false}}
function Test-EngineerOS{try{$r=Invoke-WebRequest -UseBasicParsing -Uri $AppUrl -TimeoutSec 2 -MaximumRedirection 0;return $r.StatusCode -eq 200 -and $r.Content -match 'ENGINEER OS'}catch{return $false}}
function Wait-Http([string]$u,[int]$t,[string]$n){$d=(Get-Date).AddSeconds($t);do{if(Test-Http $u 2){Log "$n ready";return};Start-Sleep -Milliseconds 500}while((Get-Date)-lt$d);throw "$n did not become ready: $u"}
function Wait-EngineerOS([int]$t){$d=(Get-Date).AddSeconds($t);do{if(Test-EngineerOS){Log 'ENGINEER OS ready';return};Start-Sleep -Milliseconds 500}while((Get-Date)-lt$d);throw "ENGINEER OS did not become ready: $AppUrl"}
function Import-EnvFile([string]$p){if(!(Test-Path $p)){return};foreach($line in Get-Content -LiteralPath $p -Encoding UTF8){$x=$line.Trim();if(!$x -or $x.StartsWith('#') -or !$x.Contains('=')){continue};$a=$x.Split('=',2);$n=$a[0].Trim();$v=$a[1].Trim();if($n -match '^[A-Za-z_][A-Za-z0-9_]*$'){[Environment]::SetEnvironmentVariable($n,$v,'Process')}};Log ('Loaded '+(Split-Path -Leaf $p))}

function Ensure-Venv{
 if(Test-Path $VenvPython){& $VenvPython -c "import sys;raise SystemExit(0 if sys.version_info>=(3,12) else 2)";if($LASTEXITCODE-eq 0){return};throw 'Existing .venv uses unsupported Python'}
 Log 'Creating .venv'
 $ok=$false
 if(Get-Command py -ErrorAction SilentlyContinue){
  & py -3.13 -c "import sys;raise SystemExit(0 if sys.version_info>=(3,12) else 2)" 2>$null
  if($LASTEXITCODE-eq 0){& py -3.13 -m venv .venv;$ok=$true}
  if(!$ok){& py -3 -c "import sys;raise SystemExit(0 if sys.version_info>=(3,12) else 2)" 2>$null;if($LASTEXITCODE-eq 0){& py -3 -m venv .venv;$ok=$true}}
 }
 if(!$ok -and (Get-Command python -ErrorAction SilentlyContinue)){& python -c "import sys;raise SystemExit(0 if sys.version_info>=(3,12) else 2)" 2>$null;if($LASTEXITCODE-eq 0){& python -m venv .venv;$ok=$true}}
 if(!$ok -or !(Test-Path $VenvPython)){throw 'Python 3.12+ was not found. Install Python 3.13 x64 and run again.'}
}

function Ensure-Dependencies{
 $inputs=@('requirements-local-app.txt','requirements-pdf-review.txt')|ForEach-Object{Join-Path $RepoRoot $_}
 $fp=($inputs|ForEach-Object{(Get-FileHash -Algorithm SHA256 $_).Hash})-join ':'
 $marker=Join-Path $RuntimeDir 'requirements.sha256'
 $old=if(Test-Path $marker){(Get-Content $marker -Raw).Trim()}else{''}
 if(!$ForceDependencyCheck -and $old-eq$fp){& $VenvPython -c "import fitz" 2>$null;if($LASTEXITCODE-eq 0){Log 'Python dependencies unchanged';return}}
 Log 'Installing Python dependencies'
 & $VenvPython -m pip install --disable-pip-version-check -r (Join-Path $RepoRoot 'requirements-local-app.txt')
 if($LASTEXITCODE-ne 0){throw 'Dependency installation failed'}
 Set-Content -Encoding ASCII -Path $marker -Value $fp
}

function Ensure-Ollama{
 if(Test-Http "$OllamaUrl/api/tags" 2){Log 'Ollama already running'}else{
  $o=Get-Command ollama -ErrorAction SilentlyContinue;if(!$o){throw 'Ollama is not installed or not in PATH'}
  Log 'Starting Ollama'
  Start-Process -FilePath $o.Source -ArgumentList @('serve') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir 'ollama.out.log') -RedirectStandardError (Join-Path $LogDir 'ollama.err.log')|Out-Null
  Wait-Http "$OllamaUrl/api/tags" 45 'Ollama'
 }
 $tags=Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -TimeoutSec 10
 $names=@($tags.models|ForEach-Object{$_.name})
 if($names -notcontains $Model){
  $o=Get-Command ollama -ErrorAction Stop;Log "Downloading model $Model";& $o.Source pull $Model
  if($LASTEXITCODE-ne 0){throw "Ollama model pull failed: $Model"}
 }else{Log "Model ready: $Model"}
}

function Find-OpenWebUI{
 $ow=Get-Command open-webui -ErrorAction SilentlyContinue
 if($ow){return $ow.Source}
 $candidates=@(
  (Join-Path $env:USERPROFILE '.local\bin\open-webui.exe'),
  (Join-Path $env:APPDATA 'Python\Python313\Scripts\open-webui.exe'),
  (Join-Path $env:APPDATA 'Python\Python312\Scripts\open-webui.exe'),
  (Join-Path $env:APPDATA 'Python\Python311\Scripts\open-webui.exe')
 )
 foreach($p in $candidates){if(Test-Path $p){return $p}}
 return $null
}

function Ensure-OpenWebUI{
 if($SkipOpenWebUI){Log 'Open WebUI skipped';return}
 if(Test-Http $OpenWebUIUrl 2){Log 'Open WebUI already running';return}
 $ow=Find-OpenWebUI
 if($ow){
  Log 'Starting Open WebUI'
  Start-Process -FilePath $ow -ArgumentList @('serve') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir 'openwebui.out.log') -RedirectStandardError (Join-Path $LogDir 'openwebui.err.log')|Out-Null
  try{Wait-Http $OpenWebUIUrl 60 'Open WebUI'}catch{Log ('WARNING: '+$_.Exception.Message)}
  return
 }
 $docker=Get-Command docker -ErrorAction SilentlyContinue
 if($docker){
  $container=(& $docker.Source ps -a --filter 'name=open-webui' --format '{{.Names}}' 2>$null|Select-Object -First 1)
  if($container){Log "Starting Open WebUI container: $container";& $docker.Source start $container|Out-Null;try{Wait-Http $OpenWebUIUrl 60 'Open WebUI'}catch{Log ('WARNING: '+$_.Exception.Message)};return}
 }
 Log 'WARNING: Open WebUI not detected; direct Ollama mode remains available'
}

function Ensure-EngineerOS{
 if(Test-EngineerOS){Log 'ENGINEER OS already running';return}
 $listener=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
 if($listener){throw 'Port 8765 is occupied by another application'}
 $env:ENGINEER_OS_LOCAL_PROVIDER='ollama'
 $env:ENGINEER_OS_LOCAL_MODEL_URL=$OllamaUrl
 $env:ENGINEER_OS_LOCAL_MODEL=$Model
 Log 'Starting ENGINEER OS server + built-in worker'
 Start-Process -FilePath $VenvPython -ArgumentList @('scripts\run_local_app.py','--port','8765','--no-browser') -WorkingDirectory $RepoRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir 'engineer-os.out.log') -RedirectStandardError (Join-Path $LogDir 'engineer-os.err.log')|Out-Null
 Wait-EngineerOS 60
}

try{
 Log '=== ENGINEER OS Windows one-click startup ==='
 Import-EnvFile (Join-Path $RepoRoot '.env.google-drive')
 Import-EnvFile (Join-Path $RepoRoot '.env.local')
 Ensure-Venv
 Ensure-Dependencies
 Ensure-Ollama
 Ensure-OpenWebUI
 Ensure-EngineerOS
 $postStart=Join-Path $RuntimeDir 'poststart-smoke.json'
 Log 'Running automatic post-start smoke'
 $ActiveDataDir = (& $VenvPython -X utf8 -c "from pathlib import Path;from engineering.local_app.settings import active_directory;print(active_directory(Path('.engineer-os/active-data-dir.txt'),Path('.engineer-os/local-app')))").Trim()
 if($LASTEXITCODE -ne 0){throw 'Cannot resolve selected data directory'}
 & $VenvPython (Join-Path $RepoRoot 'scripts\windows_poststart_smoke.py') --app-url $AppUrl --ollama-url $OllamaUrl --model $Model --data-dir $ActiveDataDir --out $postStart
 if($LASTEXITCODE-ne 0){throw 'Automatic post-start smoke failed; see poststart-smoke.json'}
 $state=[ordered]@{started_at=(Get-Date).ToString('o');engineer_os=$AppUrl;ollama=$OllamaUrl;open_webui=if(Test-Http $OpenWebUIUrl 2){$OpenWebUIUrl}else{$null};model=$Model;python=$VenvPython;log_dir=$LogDir;poststart_smoke=$postStart}
 $state|ConvertTo-Json|Set-Content -Encoding UTF8 (Join-Path $RuntimeDir 'startup-state.json')
 Log 'All required services ready'
 if(!$NoBrowser){Start-Process $AppUrl;Log 'Browser opened'}
 Write-Host ''
 Write-Host 'ENGINEER OS READY' -ForegroundColor Green
 Write-Host "App: $AppUrl"
 Write-Host "Logs: $LogDir"
 exit 0
}catch{
 Log ('BLOCK: '+$_.Exception.Message)
 Write-Host ''
 Write-Host 'ENGINEER OS DID NOT START' -ForegroundColor Red
 Write-Host "See: $SupervisorLog"
 exit 2
}

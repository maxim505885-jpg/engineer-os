$ErrorActionPreference='Stop'
$module=Join-Path $PSScriptRoot 'model-export.psm1'
if (-not (Test-Path $module)) { throw 'FAIL: native model exporter is not implemented' }
Import-Module $module -Force
class FixtureTable {
 [int]$Type; [string]$Name; [bool]$IsModified=$false; [int]$InitialModelPart=0
 FixtureTable([int]$typ) { $this.Type=$typ; $this.Name='fixture' }
 [void]GetContents([System.Management.Automation.PSReference]$data) {
  if($this.Type -eq 2) { $data.Value="1`t1.25`t2`t3`r`n" + ('2' * 110000) }
  else { $data.Value="1`t2`r`n" }
 }
 [void]GetParameters([System.Management.Automation.PSReference]$data) { $data.Value=@() }
}
class FixtureGroup {
 [int]$ItemCount=0
 [object]CreateNewItem([int]$typ,[object]$pars,[int]$part,[string]$name,[int]$pos) {
  if($part -ne 0 -or $pos -ne -1) { throw 'Wrong full-model parameters' }
  if($typ -eq 32) { throw 'Fixture unavailable material table' }
  return [FixtureTable]::new($typ)
 }
}
class FixtureDocument {
 [string]$PathName; [string]$Title='fixture'; [string]$Description='test'; [int]$SystemLabel=5
 [int]$LoadsValsType=0; [int]$CurrentLoadCase=1; [FixtureGroup]$AllTables=[FixtureGroup]::new()
 [bool]$Closed=$false
 [void]Close() { $this.Closed=$true }
}
class FixtureApp {
 [FixtureDocument]$Doc=[FixtureDocument]::new(); [int]$Restore=-1; [int]$Silent=-1
 [object]$MeasurementUnits=[pscustomobject]@{Geometry=1; Loads1=2}
 [object]OpenDocument([string]$path,[int]$restore,[int]$silent,[System.Management.Automation.PSReference]$msgs) {
  $this.Doc.PathName=$path; $this.Restore=$restore; $this.Silent=$silent; $msgs.Value='fixture warning'; return $this.Doc
 }
}
$root=Join-Path $env:TEMP ('engineer-export-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $root | Out-Null
try {
 $source=Join-Path $root 'source.lir'; [IO.File]::WriteAllText($source,'fixture-original')
 $before=(Get-FileHash $source).Hash; $app=[FixtureApp]::new()
 $result=Export-LiraModel -Application $app -ModelPath $source -OutputRoot $root
 if((Get-FileHash $source).Hash -ne $before) { throw 'Original changed' }
 if($app.Doc.PathName -eq $source -or $app.Restore -ne 0 -or $app.Silent -ne 1) { throw 'Unsafe model open' }
 if(-not $app.Doc.Closed) { throw 'Owned copy was not closed' }
 $manifest=Get-Content (Join-Path $result.directory 'manifest.json') -Raw | ConvertFrom-Json
 if($manifest.tables.Count -ne 31) { throw 'Missing attempted table coverage' }
 if(@($manifest.tables | Where-Object status -eq EXPORTED).Count -ne 30) { throw 'Incorrect success count' }
 if($manifest.full_information_extracted -or $manifest.results_exported -or $manifest.acceptance_granted) { throw 'Unsupported completeness claim' }
 if($manifest.solver_execution -ne 'NOT_RUN' -or -not $manifest.original_unchanged) { throw 'Unsafe provenance' }
 $node=$manifest.tables | Where-Object type_id -eq 2
 if((Get-Item (Join-Path $result.directory $node.file)).Length -le 100000) { throw 'Table preview truncation' }
 if($manifest.open_messages -ne 'fixture warning') { throw 'Lost API warning' }
 if(-not (Test-Path $result.zip)) { throw 'Missing output archive' }
 $bad=[FixtureApp]::new(); $bad.Doc.Title='irrelevant'
 try { Export-LiraModel -Application $bad -ModelPath (Join-Path $root 'missing.lir') -OutputRoot $root; throw 'Missing source accepted' }
 catch { if($_.Exception.Message -eq 'Missing source accepted') { throw } }
 Write-Output 'PASS: copy-only open, all table attempts, large tables, partial coverage, warnings, archive, original hash, owned close'
} finally { Remove-Item $root -Recurse -Force }

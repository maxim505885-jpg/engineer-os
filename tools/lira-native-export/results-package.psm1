Set-StrictMode -Version 2
function Export-LiraResultsPackage {
 [CmdletBinding()]
 param([Parameter(Mandatory=$true)]$Application, $ResultsAccess=$null,
       [Parameter(Mandatory=$true)][string]$ModelPath,
       [Parameter(Mandatory=$true)][string]$OutputRoot,
       [ValidateRange(1,50000000)][int]$MaxValues=50000000,
       [ValidateRange(1024,2147483647)][long]$MaxBytes=1073741824)
 $ErrorActionPreference='Stop'
 $source=Get-Item -LiteralPath $ModelPath
 if($source.PSIsContainer -or $source.Extension -ine '.lir'){throw 'Select a .lir file'}
 $app=$Application;$access=$ResultsAccess;$ownedAccess=$false
$batch=Join-Path $OutputRoot ('ENGINEER_OS_LIRA_RESULT_PACKAGE_'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $batch | Out-Null
$before=(Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash.ToLower()
$app=$null;$access=$null;$directory=$null
try {
 $contract=Get-Content (Join-Path $PSScriptRoot 'api-contract.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 Import-Module (Join-Path $PSScriptRoot 'model-export.psm1') -Force
 Write-Host 'Reading input tables from a private copy. No solver execution.'
 $model=Export-LiraModel -Application $app -ModelPath $source.FullName -OutputRoot $batch
 $inputManifest=Get-Content (Join-Path $model.directory 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 if(-not $inputManifest.original_unchanged){throw 'Source hash changed; result export stopped'}
 $nodeTable=$inputManifest.tables | Where-Object { $_.type_id -eq 2 -and $_.status -eq 'EXPORTED' }
 $elementTable=$inputManifest.tables | Where-Object { $_.type_id -eq 3 -and $_.status -eq 'EXPORTED' }
 if(-not $nodeTable -or -not $elementTable){throw 'Node/element IDs unavailable; ordinal IDs will not be invented'}
 function Read-SourceIDs([string]$path) {
  $ids=New-Object 'Collections.Generic.List[int]'
  $seen=New-Object 'Collections.Generic.HashSet[int]'
  $reader=New-Object IO.StreamReader($path,(New-Object Text.UTF8Encoding($false,$true)))
  try {
   while($null -ne ($line=$reader.ReadLine())) {
    if($ids.Count -ge 250000){throw 'Source ID count limit'}
    $first=($line -split "`t",2)[0]
    if($first -notmatch '^[1-9][0-9]{0,8}$'){throw 'Invalid source ID'}
    $id=[int]$first;if(-not $seen.Add($id)){throw 'Duplicate source ID'};$ids.Add($id)
   }
  } finally {$reader.Dispose()}
  return ,$ids.ToArray()
 }
 $nodes=Read-SourceIDs (Join-Path $model.directory $nodeTable.file)
 $elements=Read-SourceIDs (Join-Path $model.directory $elementTable.file)
 if(-not ('EngineerLiraResultsReader' -as [type])){Add-Type -Path (Join-Path $PSScriptRoot 'results-reader.cs') -ReferencedAssemblies System.Web.Extensions,System.Core}
 if($null -eq $access){$access=[Activator]::CreateInstance([type]::GetTypeFromCLSID([guid]$contract.results_clsid,$true));$ownedAccess=$true}
 Write-Host 'Reading saved result values; this may take time. Progress is printed per category.'
 $title=[string]$inputManifest.document.title
 $directory=[EngineerLiraResultsReader]::Export($access,$title,$before,$batch,$nodes,$elements,$MaxValues,$MaxBytes)
 $unchanged=((Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash.ToLower() -eq $before)
 $summary=Get-Content (Join-Path $directory 'summary.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 $summary | Add-Member -NotePropertyName original_unchanged -NotePropertyValue $unchanged
 if(-not $unchanged){$summary.status='SOURCE_CHANGED'}
 $summary | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $directory 'summary.json') -Encoding UTF8
 if(-not (Get-ChildItem $directory -Directory)) {
  $diagnostic=Join-Path $directory 'part_001';New-Item -ItemType Directory $diagnostic | Out-Null
  $summary | Add-Member -NotePropertyName files -NotePropertyValue @()
  $summary | ConvertTo-Json -Depth 20 | Set-Content (Join-Path $diagnostic 'manifest.json') -Encoding UTF8
 }
 foreach($part in (Get-ChildItem $directory -Directory)) {
  $manifestPath=Join-Path $part.FullName 'manifest.json'
  $manifest=Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $manifest | Add-Member -NotePropertyName original_unchanged -NotePropertyValue $unchanged -Force
  if(-not $unchanged){$manifest.status='SOURCE_CHANGED'}
  $manifest | ConvertTo-Json -Depth 20 | Set-Content $manifestPath -Encoding UTF8
  Copy-Item (Join-Path $PSScriptRoot 'results-contract.json') (Join-Path $part.FullName 'api-contract.json')
  Compress-Archive -Path (Join-Path $part.FullName '*') -DestinationPath (Join-Path $batch ($part.Name+'.zip'))
 }
 Copy-Item (Join-Path $directory 'summary.json') (Join-Path $batch 'RESULT_SUMMARY.json')
 Write-Host ('STATUS: '+$summary.status+'; values: '+$summary.value_rows+'; unavailable: '+$summary.unavailable_values)
 Write-Host ('READY: '+$batch)
 Write-Host 'Send RESULT_SUMMARY.json and part_*.zip. The model ZIP is a separate input-table export.'
 return $batch
} catch {
 [ordered]@{schema=1;kind='ENGINEER_OS_LIRA_RESULTS_EXPORT';status='RESULT_EXPORT_FAILED';
  error=$_.Exception.GetBaseException().Message;source_sha256=$before;solver_execution='NOT_RUN';
  source_result_binding_verified=$false;full_information_extracted=$false;acceptance_granted=$false} |
  ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $batch 'RESULT_ERROR.json') -Encoding UTF8
 Write-Host ('ERROR REPORT: '+$batch)
 throw
} finally {
 if($ownedAccess -and $null -ne $access -and [Runtime.InteropServices.Marshal]::IsComObject($access)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($access)}
}
}
Export-ModuleMember -Function Export-LiraResultsPackage

param([string]$ModelPath='', [string]$OutputRoot='', [switch]$NoExplorer,
      [ValidateRange(1,50000000)][int]$MaxValues=50000000,
      [ValidateRange(1024,2147483647)][long]$MaxBytes=1073741824)
$ErrorActionPreference='Stop'
if([Environment]::OSVersion.Platform -ne 'Win32NT' -or [IntPtr]::Size -ne 8) {throw '64-bit Windows PowerShell is required'}
if(-not $ModelPath) {
 Add-Type -AssemblyName System.Windows.Forms
 $dialog=New-Object Windows.Forms.OpenFileDialog
 $dialog.Filter='LIRA model (*.lir)|*.lir';$dialog.Title='ENGINEER OS: model with saved calculation results'
 if($dialog.ShowDialog() -ne [Windows.Forms.DialogResult]::OK){exit 0}
 $ModelPath=$dialog.FileName
}
$source=Get-Item -LiteralPath $ModelPath
if($source.PSIsContainer -or $source.Extension -ine '.lir'){throw 'Select a .lir file'}
if(-not $OutputRoot){$OutputRoot=[Environment]::GetFolderPath('Desktop')}
$app=$null;$batch=$null
try {
 $contract=Get-Content (Join-Path $PSScriptRoot 'api-contract.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 Import-Module (Join-Path $PSScriptRoot 'results-package.psm1') -Force
 $app=[Activator]::CreateInstance([type]::GetTypeFromCLSID([guid]$contract.application_clsid,$true))
 $batch=Export-LiraResultsPackage -Application $app -ModelPath $source.FullName -OutputRoot $OutputRoot -MaxValues $MaxValues -MaxBytes $MaxBytes
} catch {
 $batch=Join-Path $OutputRoot ('ENGINEER_OS_LIRA_RESULT_ERROR_'+[guid]::NewGuid().ToString('N'))
 New-Item -ItemType Directory -Path $batch -Force | Out-Null
 [ordered]@{schema=1;kind='ENGINEER_OS_LIRA_RESULTS_EXPORT';status='RESULT_EXPORT_FAILED';
  error=$_.Exception.GetBaseException().Message;source_sha256=(Get-FileHash -LiteralPath $source.FullName).Hash.ToLower();
  solver_execution='NOT_RUN';full_information_extracted=$false;source_result_binding_verified=$false;acceptance_granted=$false} |
  ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $batch 'RESULT_ERROR.json') -Encoding UTF8
 Write-Host ('ERROR REPORT: '+$batch)
 throw
} finally {
 if($null -ne $app -and [Runtime.InteropServices.Marshal]::IsComObject($app)){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
 if(-not $NoExplorer){$folder=if($batch){$batch}else{$OutputRoot};Start-Process explorer.exe -ArgumentList ('"'+$folder+'"')}
}

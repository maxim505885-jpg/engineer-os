param([string]$ModelPath='', [string]$OutputRoot='', [switch]$NoExplorer)
$ErrorActionPreference='Stop'
if([Environment]::OSVersion.Platform -ne 'Win32NT') { throw 'Windows is required' }
if([IntPtr]::Size -ne 8) { throw '64-bit PowerShell is required' }
if(-not $ModelPath) {
 Add-Type -AssemblyName System.Windows.Forms
 $dialog=New-Object Windows.Forms.OpenFileDialog
 $dialog.Filter='LIRA model (*.lir)|*.lir'; $dialog.Title='Select LIRA model for ENGINEER OS'
 if($dialog.ShowDialog() -ne [Windows.Forms.DialogResult]::OK) { exit 0 }
 $ModelPath=$dialog.FileName
}
# Validate source before COM activation.
$file=Get-Item -LiteralPath $ModelPath
if($file.PSIsContainer -or $file.Extension -ine '.lir') { throw 'Select a .lir file' }
if(-not $OutputRoot) { $OutputRoot=[Environment]::GetFolderPath('Desktop') }
$contract=Get-Content (Join-Path $PSScriptRoot 'api-contract.json') -Raw -Encoding UTF8 | ConvertFrom-Json
Import-Module (Join-Path $PSScriptRoot 'model-export.psm1') -Force
$app=$null
try {
 $type=[type]::GetTypeFromCLSID([guid]$contract.application_clsid,$true)
 $app=[Activator]::CreateInstance($type)
 $result=Export-LiraModel -Application $app -ModelPath $file.FullName -OutputRoot $OutputRoot
 Write-Host ('READY: '+$result.zip)
 Write-Host ('STATUS: '+$result.status)
 Write-Host ('TABLES: '+$result.exported_tables+' exported; '+$result.unavailable_tables+' unavailable')
 if(-not $NoExplorer) { Start-Process explorer.exe -ArgumentList ('/select,"'+$result.zip+'"') }
} catch {
 $errorFile=Join-Path $OutputRoot ('ENGINEER_OS_LIRA_EXPORT_ERROR_'+[guid]::NewGuid().ToString('N')+'.json')
 [ordered]@{status='EXPORT_FAILED'; error=$_.Exception.Message; solver_execution='NOT_RUN'; acceptance_granted=$false} |
  ConvertTo-Json | Set-Content -LiteralPath $errorFile -Encoding UTF8
 Write-Host ('ERROR REPORT: '+$errorFile)
 if(-not $NoExplorer) { Start-Process explorer.exe -ArgumentList ('/select,"'+$errorFile+'"') }
 throw
} finally {
 if($null -ne $app -and [Runtime.InteropServices.Marshal]::IsComObject($app)) {
  [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)
 }
}

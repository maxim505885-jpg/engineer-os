Set-StrictMode -Version 2
function Export-LiraModel {
 [CmdletBinding()]
 param([Parameter(Mandatory=$true)]$Application,
       [Parameter(Mandatory=$true)][string]$ModelPath,
       [Parameter(Mandatory=$true)][string]$OutputRoot)
 $ErrorActionPreference='Stop'
 $source=(Get-Item -LiteralPath $ModelPath).FullName
 if([IO.Path]::GetExtension($source) -ine '.lir') { throw 'Expected a .lir model' }
 $contract=Get-Content (Join-Path $PSScriptRoot 'api-contract.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 $originalHash=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLower()
 $id=[guid]::NewGuid().ToString('N')
 $directory=Join-Path $OutputRoot ('ENGINEER_OS_LIRA_EXPORT_'+$id)
 $working=Join-Path $OutputRoot ('ENGINEER_OS_LIRA_COPY_'+$id)
 New-Item -ItemType Directory -Path $directory,$working | Out-Null
 $copy=Join-Path $working ([IO.Path]::GetFileName($source))
 Copy-Item -LiteralPath $source -Destination $copy
 if((Get-FileHash -LiteralPath $copy).Hash.ToLower() -ne $originalHash) { throw 'Source changed during copy' }
 $manifest=[ordered]@{
  schema=1; kind='ENGINEER_OS_LIRA_MODEL_TABLE_EXPORT'; created_utc=[DateTime]::UtcNow.ToString('o');
  source_name=[IO.Path]::GetFileName($source); source_bytes=(Get-Item -LiteralPath $source).Length;
  source_sha256=$originalHash; inventory_sha256=$contract.inventory_sha256;
  status='NOT_OPENED'; open_messages=''; document=$null; units=[ordered]@{};
  tables=@(); existing_table_count=$null; errors=@(); original_unchanged=$false;
  owned_document_closed=$false; full_information_extracted=$false; results_exported=$false;
  solver_execution='NOT_RUN'; acceptance_granted=$false;
  limitations=@('Only default-parameter whole-model input tables are attempted.',
    'Parameter-dependent variants, load records and non-table binary sections are not exhaustively extracted.',
    'Existing saved input tables are not exported separately; generated tables represent the loaded model.',
    'Soil binary, completed results and their link to the model require separate processing.',
    'No result requests or solver execution. No engineering acceptance.')
 }
 $doc=$null
 try {
  $messages=''
  # RestoreEnv=0 prevents unpacking/overwriting associated input files.
  # Silent=1; messages remain in the manifest. Only the private copy is opened.
  $doc=$Application.OpenDocument($copy,0,1,[ref]$messages)
  $manifest.open_messages=[string]$messages
  if($null -eq $doc) { throw 'OpenDocument returned no document' }
  if(-not [string]::Equals([IO.Path]::GetFullPath([string]$doc.PathName),[IO.Path]::GetFullPath($copy),[StringComparison]::OrdinalIgnoreCase)) {
   $doc=$null; throw 'API returned a different document; it will not be closed or read'
  }
  $manifest.document=[ordered]@{title=[string]$doc.Title; description=[string]$doc.Description;
   system_label=[int]$doc.SystemLabel; load_values_type=[int]$doc.LoadsValsType; current_load_case=[int]$doc.CurrentLoadCase}
  foreach($name in $contract.unit_properties) {
   try { $manifest.units[$name]=$Application.MeasurementUnits.$name }
   catch { $manifest.units[$name]=[ordered]@{status='UNAVAILABLE'; error=$_.Exception.Message} }
  }
  $group=$doc.AllTables
  $manifest.existing_table_count=[int]$group.ItemCount
  foreach($spec in $contract.tables) {
   $record=[ordered]@{type_id=[int]$spec.id; api_name=$spec.name; description=$spec.description;
    status='NOT_ATTEMPTED'; file=$null; sha256=$null; bytes=0; model_part=0;
    parameters=$null; parameter_status='UNAVAILABLE'; error=$null}
   try {
    # Creates an input-table view from the model; never calls SetContents/Apply/Save.
    $table=$group.CreateNewItem([int]$spec.id,$null,0,('ENGINEER_OS_'+$spec.id),-1)
    if($null -eq $table) { throw 'CreateNewItem returned no table' }
    if([int]$table.Type -ne [int]$spec.id -or [int]$table.InitialModelPart -ne 0) { throw 'Unexpected table type or model subset' }
    $data=''; $table.GetContents([ref]$data)
    if($null -eq $data) { throw 'GetContents returned null, not an empty table' }
    if($data -isnot [string]) { throw 'Expected API tab-separated string; unsupported return shape' }
    $filename=('table_{0:D2}.tsv' -f [int]$spec.id)
    $file=Join-Path $directory $filename
    [IO.File]::WriteAllText($file,$data,(New-Object Text.UTF8Encoding($false)))
    $record.file=$filename; $record.bytes=(Get-Item -LiteralPath $file).Length
    $record.sha256=(Get-FileHash -LiteralPath $file).Hash.ToLower(); $record.status='EXPORTED'
    $pars=$null
    try { $table.GetParameters([ref]$pars); $record.parameters=$pars; $record.parameter_status='READ' }
    catch { $record.parameter_status='UNAVAILABLE: '+$_.Exception.Message }
   } catch { $record.status='UNAVAILABLE'; $record.error=$_.Exception.Message }
   $manifest.tables+=,$record
  }
  $manifest.status='PARTIAL_MODEL_TABLE_EXPORT'
 } catch { $manifest.status='MODEL_ACCESS_FAILED'; $manifest.errors+=,$_.Exception.Message }
 finally {
  if($null -ne $doc) {
   try { $doc.Close(); $manifest.owned_document_closed=$true }
   catch { $manifest.errors+=('Could not close owned copy: '+$_.Exception.Message) }
  }
  $manifest.original_unchanged=((Get-FileHash -LiteralPath $source).Hash.ToLower() -eq $originalHash)
  if(-not $manifest.original_unchanged) { $manifest.status='SOURCE_CHANGED'; $manifest.errors+='Original hash changed during export' }
 }
 $manifest | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath (Join-Path $directory 'manifest.json') -Encoding UTF8
 $zip=$directory+'.zip'
 Compress-Archive -Path (Join-Path $directory '*') -DestinationPath $zip
 # Leave the private model copy on disk; never remove a file still open in LIRA.
 return [pscustomobject]@{directory=$directory; zip=$zip; status=$manifest.status; working_copy=$copy;
  exported_tables=@($manifest.tables | Where-Object status -eq EXPORTED).Count;
  unavailable_tables=@($manifest.tables | Where-Object status -eq UNAVAILABLE).Count}
}
Export-ModuleMember -Function Export-LiraModel

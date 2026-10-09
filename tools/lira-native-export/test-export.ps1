$ErrorActionPreference='Stop'
$module=Join-Path $PSScriptRoot 'model-export.psm1'
Add-Type -TypeDefinition @'
using System;
using System.Reflection;
using System.Runtime.InteropServices;
public class ExportFixtureTable {
 public int Type {get;set;} public string Name {get;set;} public bool IsModified {get{return false;}}
 public int InitialModelPart {get{return 0;}}
 public ExportFixtureTable(int typ) {Type=typ;Name="fixture";}
 public void GetContents(ref object data) {
  if (!(data is string)) throw new ArgumentException("Expected string in ref VARIANT");
  data=Type==2 ? "1\t1.25\t2\t3\r\n"+new string('2',110000) : "1\t2\r\n";
 }
 public void GetParameters(ref object data) {data=new object[0];}
}
public class ExportFixtureGroup {
 public int ItemCount {get{return 0;}} public bool AllUnavailable;
 public object CreateNewItem(int typ, [Optional] object pars, int part, string name, int pos) {
  if(!Object.ReferenceEquals(pars,Missing.Value)) throw new COMException("Wrong optional VARIANT",unchecked((int)0x80020005));
  if(part!=0||pos!=-1) throw new ArgumentException("Wrong whole-model parameters");
  if(AllUnavailable||typ==32) throw new COMException("Unavailable fixture",unchecked((int)0x80020005));
  return new ExportFixtureTable(typ);
 }
}
public class ExportFixtureDocument {
 public string PathName {get;set;} public string Title {get{return "fixture";}}
 public string Description {get{return "test";}} public int SystemLabel {get{return 5;}}
 public int LoadsValsType {get{return 0;}} public int CurrentLoadCase {get{return 1;}}
 public ExportFixtureGroup AllTables {get;set;}
 public ExportFixtureDocument(){AllTables=new ExportFixtureGroup();}
 public bool Closed; public void Close(){Closed=true;}
}
public class ExportFixtureUnits {public int Geometry {get{return 1;}} public int Loads1 {get{return 2;}}}
public class ExportFixtureApp {
 public ExportFixtureDocument Doc=new ExportFixtureDocument(); public int Restore=-1,Silent=-1;
 public ExportFixtureUnits MeasurementUnits {get{return new ExportFixtureUnits();}}
 public object OpenDocument(string path,int restore,int silent,ref string msgs) {
  Doc.PathName=path;Restore=restore;Silent=silent;msgs="fixture warning";return Doc;
 }
}
'@
Import-Module $module -Force
$root=Join-Path $env:TEMP ('engineer-export-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $root | Out-Null
try {
 $source=Join-Path $root 'source.lir'; [IO.File]::WriteAllText($source,'fixture-original')
 $before=(Get-FileHash $source).Hash; $app=New-Object ExportFixtureApp
 $result=Export-LiraModel -Application $app -ModelPath $source -OutputRoot $root
 if((Get-FileHash $source).Hash -ne $before) { throw 'Original changed' }
 if($app.Doc.PathName -eq $source -or $app.Restore -ne 0 -or $app.Silent -ne 1) { throw 'Unsafe model open' }
 if(-not $app.Doc.Closed) { throw 'Owned copy was not closed' }
 $manifest=Get-Content (Join-Path $result.directory 'manifest.json') -Raw | ConvertFrom-Json
 if(@($manifest.tables | Where-Object status -eq EXPORTED).Count -ne 30) { throw 'FAIL: optional VARIANT produced no tables' }
 if($manifest.tables.Count -ne 31) { throw 'Missing table coverage' }
 if($manifest.full_information_extracted -or $manifest.results_exported -or $manifest.acceptance_granted) { throw 'Unsupported completeness claim' }
 if($manifest.solver_execution -ne 'NOT_RUN' -or -not $manifest.original_unchanged) { throw 'Unsafe provenance' }
 $node=$manifest.tables | Where-Object type_id -eq 2
 if((Get-Item (Join-Path $result.directory $node.file)).Length -le 100000) { throw 'Truncated output' }
 if($manifest.open_messages -ne 'fixture warning' -or -not (Test-Path $result.zip)) { throw 'Missing warning/archive' }
 $bad=New-Object ExportFixtureApp; $bad.Doc.AllTables.AllUnavailable=$true
 $badResult=Export-LiraModel -Application $bad -ModelPath $source -OutputRoot $root
 $failed=Get-Content (Join-Path $badResult.directory 'manifest.json') -Raw | ConvertFrom-Json
 if($failed.status -ne 'TABLE_EXPORT_FAILED') { throw 'FAIL: zero-table export incorrectly labelled partial success' }
 foreach($t in $failed.tables) {
  if($t.error_stage -ne 'CREATE_TABLE' -or $t.error_hresult -ne '0x80020005') { throw 'Missing error stage/HRESULT' }
 }
 # Verify actual Windows native VARIANT representation, not only managed stubs.
 $pointer=[Runtime.InteropServices.Marshal]::AllocCoTaskMem(32)
 try {
  [Runtime.InteropServices.Marshal]::GetNativeVariantForObject([Reflection.Missing]::Value,$pointer)
  if([Runtime.InteropServices.Marshal]::ReadInt16($pointer) -ne 10 -or [Runtime.InteropServices.Marshal]::ReadInt32($pointer,8) -ne -2147352572) { throw 'Missing argument was not VT_ERROR/DISP_E_PARAMNOTFOUND' }
 } finally { [Runtime.InteropServices.Marshal]::FreeCoTaskMem($pointer) }
 Write-Output 'PASS: optional VARIANT, ref object return, zero-table failure, stage/HRESULT, native Missing encoding, copy integrity, large tables'
} finally { Remove-Item $root -Recurse -Force }

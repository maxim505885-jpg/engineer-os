$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class ResNumbers {
 public int[] Values; public int Count {get{return Values.Length;}}
 public int this[int i] {get{return Values[i];}}
 public ResNumbers(params int[] values){Values=values;}
 public void AddFromString(string ids) { }
}
public class ResRequest {
 public string DocumentName {get;set;} public int SuperElement {get;set;}
 public ResNumbers Nodes {get{return new ResNumbers();}}
 public ResNumbers Elements {get{return new ResNumbers();}}
}
public class ResCase {public int Number {get{return 7;}}}
public class ResCases {
 public int Count {get{return 1;}}
 public ResCase this[int i] {get{if(i!=0)throw new Exception("Wrong case ordinal");return new ResCase();}}
}
public class ResResponse {
 public ResCases LoadCases {get{return new ResCases();}}
 public ResNumbers NodeNumbers {get{return new ResNumbers(101);}}
 public ResNumbers ElementNumbers {get{return new ResNumbers(205);}}
 public ResNumbers Directions {get{return new ResNumbers(1,3);}}
 public ResNumbers Forces {get{return new ResNumbers(1,3);}}
 public int GetNodeCount(){return 1;} public int GetElementCount(){return 1;} public int GetHistoryCount(){return 0;}
 public double GetNodeX(int n,int lc,int shape,int history){if(n!=101||lc!=7||shape!=0||history!=0)throw new Exception("Wrong context");return 0.125;}
 public double GetNodeZ(int n,int lc,int shape,int history){throw new COMException("Unavailable Z",unchecked((int)0x80004005));}
 public int GetSectionCount(int n){return 2;}
 public ResNumbers GetForces(int n){return new ResNumbers(1);}
 public int GetFamily(int n){return 1;} public int GetType(int n){return 10;}
 public float GetBarN(int n,int cs,int lc,int shape,int history){return 1.5f*cs;}
 public double GetNodeRX(int n,int lc,int shape){return 2.5;}
 public double GetNodeRZ(int n,int lc,int shape){return 3.5;}
 public double GetNodeN(int n,int lc,int shape){return 4.5;}
 public double GetNodeMY(int n,int lc,int shape){return 5.5;}
 public ResNumbers LoadCaseNumbers {get{return new ResNumbers(7);}}
 public ResNumbers GetPeriods(int lc){return new ResNumbers(2);}
}
public class ResAccess {
 public bool AllUnavailable; public List<int> Requested=new List<int>();
 public object CreateNewRequest(int kind){Requested.Add(kind);return new ResRequest();}
 private object Response(){if(AllUnavailable)throw new COMException("No results",unchecked((int)0x80004005));return new ResResponse();}
 public object MainData(object r){return Response();}
 public object LoadCaseDisplacements(object r){return Response();}
 public object LoadCaseForces(object r){return Response();}
 public object FragmLoads(object r){return Response();}
 public object PunchLoads(object r){return Response();}
 public object LoadCombinationForces(object r){return Response();}
 public object LoadCombinationDisplacements(object r){return Response();}
 public object DesignCombinationForces(object r){return Response();}
 public object PeriodsOfVibrations(object r){return Response();}
 public object SelectedReinforcement(object r){return Response();}
}
'@
$reader=Join-Path $PSScriptRoot 'results-reader.cs'
if(-not(Test-Path $reader)){throw 'RED: results reader not implemented'}
Add-Type -Path $reader -ReferencedAssemblies System.Web.Extensions
$root=Join-Path $env:TEMP ('engineer-results-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $root | Out-Null
try {
 $access=New-Object ResAccess
 $result=[EngineerLiraResultsReader]::Export($access,'fixture',('a'*64),$root,[int[]]@(101),[int[]]@(205),1000,5000000)
 $summary=Get-Content (Join-Path $result 'summary.json') -Raw | ConvertFrom-Json
 if($summary.full_information_extracted -or $summary.acceptance_granted -or $summary.source_result_binding_verified -or $summary.completed_solver_run_verified){throw 'False acceptance/binding/completion'}
 if($summary.solver_execution -ne 'NOT_RUN'){throw 'Solver claim'}
 if($summary.value_rows -lt 5){throw 'Missing numerical results'}
 if($summary.unavailable_values -lt 1){throw 'Missing unavailable scalar provenance'}
 if($summary.requests.Count -ne 10){throw 'Incomplete request inventory'}
 $files=Get-ChildItem $result -Filter '*.tsv' -Recurse
 $text=($files | ForEach-Object {[IO.File]::ReadAllText($_.FullName)}) -join "`n"
 if($text -notmatch "101`t7`t0`t0" -or $text -notmatch '0.125'){throw 'Sparse IDs, actual LC number or invariant values lost'}
 if($text -notmatch 'UNAVAILABLE' -or $text -notmatch '0x80004005'){throw 'Error was replaced with numerical zero'}
 foreach($part in (Get-ChildItem $result -Directory)) {
  $manifest=Get-Content (Join-Path $part.FullName 'manifest.json') -Raw | ConvertFrom-Json
  foreach($file in $manifest.files){if((Get-FileHash (Join-Path $part.FullName $file.file)).Hash.ToLower() -ne $file.sha256){throw 'Bad payload hash'}}
 }
 $limited=[EngineerLiraResultsReader]::Export((New-Object ResAccess),'fixture',('a'*64),$root,[int[]]@(101),[int[]]@(205),1,5000000)
 $budget=Get-Content (Join-Path $limited 'summary.json') -Raw | ConvertFrom-Json
 if($budget.status -ne 'BUDGET_EXHAUSTED' -or $budget.attempted_values -ne 1){throw 'Budget not enforced'}
 $bad=New-Object ResAccess; $bad.AllUnavailable=$true
 $none=[EngineerLiraResultsReader]::Export($bad,'fixture',('a'*64),$root,[int[]]@(101),[int[]]@(205),1000,5000000)
 $empty=Get-Content (Join-Path $none 'summary.json') -Raw | ConvertFrom-Json
 if($empty.status -ne 'RESULT_ACCESS_UNAVAILABLE' -or $empty.value_rows -ne 0){throw 'No-result export misreported success'}
 Write-Output 'PASS: 10 request types, sparse IDs, LC numbers, exact arguments, scalar failures, output hashes, limits, no false completion'
} finally {Remove-Item -LiteralPath $root -Recurse -Force}

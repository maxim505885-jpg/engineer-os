param([string]$InstallDir = '', [string]$OutputRoot = '', [switch]$NoExplorer)
$ErrorActionPreference = 'Stop'
if ([Environment]::OSVersion.Platform -ne 'Win32NT') { throw 'Windows is required.' }
if (-not $OutputRoot) { $OutputRoot = [Environment]::GetFolderPath('Desktop') }
$folder = Join-Path $OutputRoot ('ENGINEER_OS_LIRA_API_' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $folder | Out-Null

# Read type libraries only. No COM activation, solver, registry writes, or model edits.
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Linq;
using TYPEATTR = System.Runtime.InteropServices.ComTypes.TYPEATTR;
using FUNCDESC = System.Runtime.InteropServices.ComTypes.FUNCDESC;
using VARDESC = System.Runtime.InteropServices.ComTypes.VARDESC;
using VARKIND = System.Runtime.InteropServices.ComTypes.VARKIND;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
public static class EngineerLiraTypeLibrary {
    [DllImport("oleaut32.dll", CharSet=CharSet.Unicode, PreserveSig=false)]
    private static extern void LoadTypeLibEx(string file, int regkind, out ITypeLib library);
    public static object Read(string file) {
        ITypeLib lib; LoadTypeLibEx(file, 2, out lib); // REGKIND_NONE
        try {
            int count = lib.GetTypeInfoCount();
            if (count > 2000) throw new InvalidOperationException("Type inventory limit");
            string name, doc, help; int context;
            lib.GetDocumentation(-1, out name, out doc, out context, out help);
            var types = new List<object>(); int totalMembers = 0;
            for (int i=0; i<count; i++) {
                ITypeInfo ti; lib.GetTypeInfo(i, out ti);
                try {
                    IntPtr attrPtr; ti.GetTypeAttr(out attrPtr);
                    TYPEATTR attr;
                    try { attr=(TYPEATTR)Marshal.PtrToStructure(attrPtr, typeof(TYPEATTR)); }
                    finally { ti.ReleaseTypeAttr(attrPtr); }
                    if (attr.cFuncs>1000 || attr.cVars>2000 || totalMembers+attr.cFuncs+attr.cVars>100000)
                        throw new InvalidOperationException("Member inventory limit");
                    totalMembers += attr.cFuncs+attr.cVars;
                    ti.GetDocumentation(-1, out name, out doc, out context, out help);
                    var funcs = new List<object>(); var vars = new List<object>();
                    for (int f=0; f<attr.cFuncs; f++) {
                        IntPtr ptr; ti.GetFuncDesc(f, out ptr);
                        try {
                            var d=(FUNCDESC)Marshal.PtrToStructure(ptr, typeof(FUNCDESC));
                            if (d.cParams>128) throw new InvalidOperationException("Parameter inventory limit");
                            string[] names=new string[129]; int got; ti.GetNames(d.memid,names,129,out got);
                            string fn, description, hf; int hc;
                            ti.GetDocumentation(d.memid,out fn,out description,out hc,out hf);
                            funcs.Add(new Dictionary<string,object> {
                                {"name",fn}, {"description",description}, {"member_id",d.memid},
                                {"invoke_kind",d.invkind.ToString()}, {"parameters",new ArraySegment<string>(names,Math.Min(1,got),Math.Max(0,got-1)).ToArray()},
                                {"parameter_count",d.cParams}, {"optional_parameters",d.cParamsOpt},
                                {"return_variant_type",d.elemdescFunc.tdesc.vt}
                            });
                        } finally { ti.ReleaseFuncDesc(ptr); }
                    }
                    for (int v=0; v<attr.cVars; v++) {
                        IntPtr ptr; ti.GetVarDesc(v,out ptr);
                        try {
                            var d=(VARDESC)Marshal.PtrToStructure(ptr,typeof(VARDESC));
                            string vn, vd, vh; int vc; ti.GetDocumentation(d.memid,out vn,out vd,out vc,out vh);
                            object value=null;
                            if (d.varkind==VARKIND.VAR_CONST && d.desc.lpvarValue!=IntPtr.Zero) {
                                var raw=Marshal.GetObjectForNativeVariant(d.desc.lpvarValue);
                                if (raw==null || raw is string || raw is ValueType) value=raw;
                            }
                            vars.Add(new Dictionary<string,object> { {"name",vn}, {"description",vd}, {"kind",d.varkind.ToString()}, {"constant",value} });
                        } finally { ti.ReleaseVarDesc(ptr); }
                    }
                    types.Add(new Dictionary<string,object> { {"name",name}, {"guid",attr.guid.ToString()},
                        {"kind",attr.typekind.ToString()}, {"methods",funcs}, {"variables",vars} });
                } finally { Marshal.ReleaseComObject(ti); }
            }
            lib.GetDocumentation(-1,out name,out doc,out context,out help);
            return new Dictionary<string,object> { {"name",name}, {"description",doc}, {"types",types}, {"members",totalMembers} };
        } finally { Marshal.ReleaseComObject(lib); }
    }
}
'@

$roots = New-Object 'System.Collections.Generic.List[string]'
if ($InstallDir) { $roots.Add((Resolve-Path -LiteralPath $InstallDir).Path) }
else {
    foreach ($p in @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^Lira(Sapr|Fem)$' })) {
        try { if ($p.Path) { $roots.Add((Split-Path -Parent $p.Path)) } } catch { }
    }
    foreach ($base in @(${env:ProgramFiles(x86)},$env:ProgramFiles)) {
        if (-not $base) { continue }
        foreach ($relative in @('LIRA SAPR\LIRA SAPR 2024\Bin\x64','LIRA SAPR\LIRA SAPR 2024 DEMO\Bin\x64','LIRALAND\LIRA-FEM 2025\Bin\x64','LIRALAND\LIRA-FEM 2026\Bin\x64')) {
            $candidate=Join-Path $base $relative
            if (Test-Path -LiteralPath $candidate -PathType Container) { $roots.Add($candidate) }
        }
    }
}
$files = @()
foreach ($root in @($roots | Select-Object -Unique -First 16)) {
    $files += @(Get-ChildItem -LiteralPath $root -File | Where-Object { $_.Name -match '^(LiraSapr|LiraFem)\.exe$|^Lira.*(API|Res).*\.dll$|^Lira.*\.tlb$' })
}
$files = @($files | Sort-Object FullName -Unique | Select-Object -First 32)
$records = @()
foreach ($file in $files) {
    $entry = [ordered]@{path=$file.FullName; bytes=$file.Length; sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower(); status='NOT_READ'; type_library=$null; error=$null}
    if ($file.Length -gt 512MB) { $entry.status='FILE_LIMIT' }
    else {
        try { $entry.type_library=[EngineerLiraTypeLibrary]::Read($file.FullName); $entry.status='TYPE_LIBRARY_READ' }
        catch { $entry.status='TYPE_LIBRARY_UNAVAILABLE'; $entry.error=$_.Exception.Message }
    }
    $records += $entry
}
$report = [ordered]@{
    schema=1; scope='INSTALLED_API_INVENTORY_ONLY'; created_utc=[DateTime]::UtcNow.ToString('o');
    pointer_bits=([IntPtr]::Size*8); libraries=$records; status='API_NOT_FOUND';
    source_model_opened=$false; model_exported=$false; results_exported=$false;
    solver_execution='NOT_RUN'; acceptance_granted=$false;
    next='Validate model-open/table-read methods against the installed type library before invoking them.'
}
if (@($records | Where-Object {$_.status -eq 'TYPE_LIBRARY_READ'}).Count -gt 0) { $report.status='API_INVENTORY_RECORDED' }
$report | ConvertTo-Json -Depth 18 | Set-Content -LiteralPath (Join-Path $folder 'lira-api-inventory.json') -Encoding UTF8
$zip = $folder + '.zip'
Compress-Archive -LiteralPath (Join-Path $folder 'lira-api-inventory.json') -DestinationPath $zip
Write-Host ('READY: ' + $zip)
Write-Host ('STATUS: ' + $report.status)
if (-not $NoExplorer) { Start-Process explorer.exe -ArgumentList ('/select,"' + $zip + '"') }

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;

// LIRA SAPR 2024: late binding avoids installing compiler interop assemblies.
// Only primary shape=0/history=0 values; other contexts remain explicitly open.
public static class EngineerLiraResultsReader {
 static readonly string[] RequestMethods={"","LoadCaseDisplacements","LoadCaseForces","FragmLoads","PunchLoads","LoadCombinationForces","LoadCombinationDisplacements","DesignCombinationForces","PeriodsOfVibrations","SelectedReinforcement","MainData"};
 static readonly string[] DirectionMethods={"","GetNodeX","GetNodeY","GetNodeZ","GetNodeUX","GetNodeUY","GetNodeUZ","GetNodeW"};
 static readonly string[] FragMethods={"","GetNodeRX","GetNodeRY","GetNodeRZ","GetNodeRUX","GetNodeRUY","GetNodeRUZ","GetNodeRBW"};
 static readonly string[] PunchMethods={"","GetNodeN","GetNodeMX","GetNodeMY","GetNodeQX","GetNodeQY","GetNodeMZ"};
 static readonly string[] ForceMethods={"","GetBarN","GetBarMx","GetBarMy","GetBarQz","GetBarMz","GetBarQy","GetBarRy","GetBarRz","GetBarBw","GetBarTw","GetPlateNx","GetPlateNy","GetPlateNz","GetPlateTxy","GetPlateTxz","GetPlateMx","GetPlateMy","GetPlateMxy","GetPlateQx","GetPlateQy","GetPlateRz","GetSolidNx","GetSolidNy","GetSolidNz","GetSolidTxy","GetSolidTxz","GetSolidTyz","GetSpecElementN","GetSpecElementNx","GetSpecElementNy","GetSpecElementNz","GetSpecElementMx","GetSpecElementMy","GetSpecElementMz","GetSpecElementQy","GetSpecElementQz","GetSpecElementRx","GetSpecElementRy","GetSpecElementRz","GetSpecElementRux","GetSpecElementRuy","GetSpecElementRuz","GetSpec_58_59_Qz","GetSpec_58_59_Ny","GetSpec_58_59_Qx","GetSpec_310_N","GetSpec_310_My","GetSpec_310_Mx","GetSpec_310_Qz","GetSpec_310_Mz","GetSpec_310_Qy","GetSpec_264_N","GetSpec_264_Qz","GetSpec_264_Qy"};
 static readonly string[] PeriodMethods={"GetFrequenciesHz","GetPeriods","GetFrequenciesRadPerSec","GetEigenvalues","GetParticipFactors","GetModalMasses","GetAccumulatedModalMasses"};
 class Budget : Exception { public Budget(string message):base(message){} }
 static object Invoke(object target,string name,BindingFlags kind,object[] args) {
  if(target==null)throw new InvalidOperationException("Null API object: "+name);
  return target.GetType().InvokeMember(name,BindingFlags.Public|BindingFlags.Instance|kind,null,target,args,null,CultureInfo.InvariantCulture,null);
 }
 static object Get(object target,string name){return Invoke(target,name,BindingFlags.GetProperty,new object[0]);}
 static object Call(object target,string name,params object[] args){return Invoke(target,name,BindingFlags.InvokeMethod,args);}
 static void Put(object target,string name,object value){Invoke(target,name,BindingFlags.SetProperty,new object[]{value});}
 static void Release(object value){if(value!=null&&Marshal.IsComObject(value))Marshal.ReleaseComObject(value);}
 static int Count(object value,int maximum){int n=Convert.ToInt32(value,CultureInfo.InvariantCulture);if(n<0||n>maximum)throw new InvalidOperationException("API count limit");return n;}
 static int[] Numbers(object array) {
  try {int n=Count(Get(array,"Count"),250000);int[] result=new int[n];for(int i=0;i<n;i++)result[i]=Convert.ToInt32(Invoke(array,"Item",BindingFlags.GetProperty,new object[]{i}),CultureInfo.InvariantCulture);return result;}
  finally {Release(array);}
 }
 static int[] Cases(object response) {
  object array=Get(response,"LoadCases");
  try {int n=Count(Get(array,"Count"),1024);int[] result=new int[n];for(int i=0;i<n;i++){object item=Invoke(array,"Item",BindingFlags.GetProperty,new object[]{i});try{result[i]=Convert.ToInt32(Get(item,"Number"),CultureInfo.InvariantCulture);}finally{Release(item);}}return result;}
  finally{Release(array);}
 }
 static Exception Root(Exception e){while(e is TargetInvocationException&&e.InnerException!=null)e=e.InnerException;return e;}
 static string HResult(Exception e){return "0x"+Root(e).HResult.ToString("X8",CultureInfo.InvariantCulture);}
 static string Message(Exception e){string s=Root(e).Message;return s.Length>240?s.Substring(0,240):s;}
 static JavaScriptSerializer Serializer(){return new JavaScriptSerializer{MaxJsonLength=4*1024*1024,RecursionLimit=32};}
 static void Json(string path,object value){File.WriteAllText(path,Serializer().Serialize(value),new UTF8Encoding(false));}
 static string Hash(string path){using(var s=File.OpenRead(path))using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(s)).Replace("-","").ToLowerInvariant();}
 static HashSet<int> IDs(int[] ids){if(ids==null||ids.Length>250000)throw new ArgumentException("Subject inventory limit");var set=new HashSet<int>();foreach(int i in ids)if(i<1||!set.Add(i))throw new ArgumentException("Invalid/duplicate subject ID");return set;}

 sealed class Output : IDisposable {
  public readonly List<string> Parts=new List<string>();
  public readonly Dictionary<string,List<object>> Files=new Dictionary<string,List<object>>();
  readonly long maximum; long total,partBytes; int fileRows,fileNumber; StreamWriter writer;string part,path;
  public Output(long maximumBytes){maximum=maximumBytes;}
  public string Root;
  void CloseFile(){if(writer==null)return;writer.Dispose();writer=null;Files[part].Add(new Dictionary<string,object>{{"file",Path.GetFileName(path)},{"bytes",new FileInfo(path).Length},{"sha256",Hash(path)},{"rows",fileRows}});}
  public void Write(string row) {
   int bytes=Encoding.UTF8.GetByteCount(row+"\n");
   if(total+bytes+256>maximum)throw new Budget("OUTPUT_BYTE_LIMIT");
   if(writer!=null&&(fileRows>=50000||partBytes+bytes>80L*1024*1024))CloseFile();
   if(writer==null) {
    if(part==null||Files[part].Count>=40||partBytes+bytes+256>80L*1024*1024){part=Path.Combine(Root,"part_"+(Parts.Count+1).ToString("D3"));Directory.CreateDirectory(part);Parts.Add(part);Files.Add(part,new List<object>());partBytes=0;}
    path=Path.Combine(part,"values_"+(++fileNumber).ToString("D5")+".tsv");writer=new StreamWriter(path,false,new UTF8Encoding(false));writer.NewLine="\n";fileRows=0;
    string header="request_type\tsubject_id\tload_case\tshape\thistory\tsection\tcomponent\tvalue\tstatus\thresult";
    writer.WriteLine(header);int hb=Encoding.UTF8.GetByteCount(header+"\n");partBytes+=hb;total+=hb;
   }
   writer.WriteLine(row);fileRows++;partBytes+=bytes;total+=bytes;
  }
  public void Dispose(){CloseFile();}
 }
 sealed class Run {
  public int Attempts,Values,Unavailable,Maximum; public Output Output;
  public void Value(int type,int id,int lc,int section,string method,Func<object> fetch) {
   if(Attempts>=Maximum)throw new Budget("API_VALUE_CALL_LIMIT");Attempts++;
   string value="",status="EXPORTED",hr="";
   try {object raw=fetch();if(raw==null||raw is bool||raw is string)throw new InvalidOperationException("Non-numeric API value");double n=Convert.ToDouble(raw,CultureInfo.InvariantCulture);if(Double.IsNaN(n)||Double.IsInfinity(n))throw new InvalidOperationException("Nonfinite API value");value=n.ToString("R",CultureInfo.InvariantCulture);}
   catch(Exception e){if(e is Budget)throw;status="UNAVAILABLE";hr=HResult(e);}
   Output.Write(String.Join("\t",new string[]{type.ToString(),id.ToString(),lc.ToString(),"0","0",section.ToString(),method,value,status,hr}));
   if(status=="EXPORTED")Values++;else Unavailable++;
  }
 }
 static void Fill(object request,string property,int[] ids) {object array=Get(request,property);try{Call(array,"AddFromString",String.Join(" ",Array.ConvertAll(ids,i=>i.ToString(CultureInfo.InvariantCulture))));}finally{Release(array);}}
 static string Component(string[] methods,int code){return code>0&&code<methods.Length?methods[code]:null;}
 static void Primary(Run run,int type,object response,int[] requested) {
  bool nodes=type!=2;var expected=IDs(requested);int[] available=Numbers(Get(response,nodes?"NodeNumbers":"ElementNumbers"));IDs(available);
  int[] cases=Cases(response);IDs(cases);
  foreach(int subject in available) {
   if(!expected.Contains(subject))throw new InvalidOperationException("Response contains unrequested subject");
   int[] codes=type==2?Numbers(Call(response,"GetForces",subject)):Numbers(Get(response,type==1?"Directions":"Forces"));
   int sections=type==2?Count(Call(response,"GetSectionCount",subject),1000):1;
   foreach(int lc in cases)for(int section=1;section<=sections;section++)foreach(int code in codes) {
    string method=type==1?(code==15?"GetNodeT":Component(DirectionMethods,code)):type==2?Component(ForceMethods,code):type==3?Component(FragMethods,code):Component(PunchMethods,code);
    if(method==null)throw new InvalidOperationException("Unknown component enum "+code);
    int id=subject,cs=section,load=lc;string name=method;
    run.Value(type,id,load,type==2?cs:0,name,()=>type==1?Call(response,name,id,load,0,0):type==2?Call(response,name,id,cs,load,0,0):Call(response,name,id,load,0));
   }
  }
 }
 public static string Export(object access,string documentName,string sourceHash,string outputRoot,int[] nodeIDs,int[] elementIDs,int maxValues,long maxBytes) {
  if(String.IsNullOrEmpty(documentName)||documentName.Length>240||documentName.IndexOfAny(new char[]{'/','\\','\r','\n'})>=0)throw new ArgumentException("DocumentName must have no path");
  if(sourceHash==null||sourceHash.Length!=64||!System.Text.RegularExpressions.Regex.IsMatch(sourceHash,"^[0-9a-fA-F]{64}$"))throw new ArgumentException("Source hash required");IDs(nodeIDs);IDs(elementIDs);
  if(maxValues<1||maxValues>50000000||maxBytes<1024||maxBytes>2L*1024*1024*1024)throw new ArgumentException("Invalid export budgets");
  string directory=Path.Combine(outputRoot,"ENGINEER_OS_LIRA_RESULTS_"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(directory);
  var requests=new List<object>();var report=new Dictionary<string,object>{{"schema",1},{"kind","ENGINEER_OS_LIRA_RESULTS_EXPORT"},{"document_name",documentName},{"source_sha256",sourceHash},{"scope","PRIMARY_SHAPE0_HISTORY0_AND_REQUEST_AVAILABILITY"},{"full_information_extracted",false},{"source_result_binding_verified",false},{"completed_solver_run_verified",false},{"engineering_verified",false},{"acceptance_granted",false},{"solver_execution","NOT_RUN"},{"requests",requests},{"requested_nodes",nodeIDs.Length},{"requested_elements",elementIDs.Length},{"limitations",new string[]{"Only primary shape 0/history 0 values; histories, dynamic forms and super-elements are not exhaustively exported.","RSN/RSU/reinforcement are availability probes, not complete value exports.","Fragment and punching loads are result quantities, not original applied-load records.","Result identity is resolved by task name; original model/result/run binding is unverified.","Native input auxiliary KE57 stiffnesses and full load records are not exposed by this export.","A returned value is not proof of a completed solver run or engineering acceptance."}}};
  var run=new Run{Maximum=maxValues};bool exhausted=false;int availableRequests=0;
  using(var output=new Output(maxBytes){Root=directory}) {
   run.Output=output;
   foreach(int type in new int[]{10,1,2,3,4,5,6,7,8,9}) {
    var item=new Dictionary<string,object>{{"type_id",type},{"method",RequestMethods[type]},{"status","NOT_ATTEMPTED"}};requests.Add(item);
    if(exhausted)continue;
    int startAttempts=run.Attempts,startValues=run.Values;int[] subjects=(type==2||type==5||type==7||type==9)?elementIDs:nodeIDs;
    if(type!=8&&type!=10&&subjects.Length==0){item["status"]="NO_SUBJECTS";continue;}
    try {
     int chunks=(type>=1&&type<=4)?Math.Max(1,(subjects.Length+127)/128):1;
     for(int chunk=0;chunk<chunks;chunk++) {
      object request=null,response=null;
      try {
       request=Call(access,"CreateNewRequest",type);Put(request,"DocumentName",documentName);Put(request,"SuperElement",0);
       int[] selected=subjects;
       if(type>=1&&type<=4){int offset=chunk*128;selected=new int[Math.Min(128,Math.Max(0,subjects.Length-offset))];Array.Copy(subjects,offset,selected,0,selected.Length);if(selected.Length==0)break;Fill(request,type==2?"Elements":"Nodes",selected);}
       // Only one explicit subject for availability probes; do not load an entire result matrix.
       if(type==5||type==7||type==9){if(subjects.Length>0)Fill(request,"Elements",new int[]{subjects[0]});}
       if(type==6){if(subjects.Length>0)Fill(request,"Nodes",new int[]{subjects[0]});}
       response=Call(access,RequestMethods[type],request);if(response==null)throw new InvalidOperationException("Null response");availableRequests++;
       if(type==10){item["nodes"]=Count(Call(response,"GetNodeCount"),250000);item["elements"]=Count(Call(response,"GetElementCount"),250000);item["histories"]=Count(Call(response,"GetHistoryCount"),10000);item["counts_match_source_inventory"]=(int)item["nodes"]==nodeIDs.Length&&(int)item["elements"]==elementIDs.Length;}
       else if(type<=4)Primary(run,type,response,selected);
       else if(type==8){foreach(int lc in Numbers(Get(response,"LoadCaseNumbers")))foreach(string method in PeriodMethods){try{object array=Call(response,method,lc);try{int n=Count(Get(array,"Count"),10000);for(int i=0;i<n;i++){int index=i;run.Value(type,index,lc,0,method,()=>Invoke(array,"Item",BindingFlags.GetProperty,new object[]{index}));}}finally{Release(array);}}catch(Budget){throw;}catch(Exception e){item[method+"_error"]=HResult(e);}}}
       item["status"]=type>=5&&type!=8?"AVAILABILITY_ONLY":"PRIMARY_VALUES_PARTIAL";
      } finally {Release(response);Release(request);}
     }
    } catch(Budget e){exhausted=true;item["status"]="BUDGET_EXHAUSTED";item["reason"]=e.Message;}
      catch(Exception e){item["status"]="UNAVAILABLE";item["error"]=Message(e);item["hresult"]=HResult(e);}
    item["attempted_values"]=run.Attempts-startAttempts;item["value_rows"]=run.Values-startValues;
    Console.WriteLine(RequestMethods[type]+": "+item["status"]+", values="+item["value_rows"]);
   }
   output.Dispose();
   report["status"]=exhausted?"BUDGET_EXHAUSTED":run.Values>0?"PARTIAL_RESULT_EXPORT":availableRequests==0?"RESULT_ACCESS_UNAVAILABLE":"NO_NUMERICAL_VALUES_EXPORTED";
   report["byte_budget_scope"]="TSV_ONLY";report["max_tsv_bytes"]=maxBytes;report["counts_scope"]="WHOLE_RUN_NOT_PART";
   report["attempted_values"]=run.Attempts;report["value_rows"]=run.Values;report["unavailable_values"]=run.Unavailable;report["result_values_exported"]=run.Values>0;report["parts"]=output.Parts.Count;
   for(int i=0;i<output.Parts.Count;i++){var part=new Dictionary<string,object>(report);part["part_number"]=i+1;part["files"]=output.Files[output.Parts[i]];Json(Path.Combine(output.Parts[i],"manifest.json"),part);}
   Json(Path.Combine(directory,"summary.json"),report);
  }
  return directory;
 }
}

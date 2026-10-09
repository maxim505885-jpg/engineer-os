using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
public sealed class NativeVariantDispatch : IDisposable {
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] private delegate int Query(IntPtr self,ref Guid iid,out IntPtr obj);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] private delegate uint Ref(IntPtr self);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] private delegate int Count(IntPtr self,out uint count);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] private delegate int Info(IntPtr self,uint index,uint lcid,out IntPtr info);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] private delegate int Names(IntPtr self,ref Guid iid,IntPtr names,uint count,uint lcid,IntPtr ids);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] private delegate int Call(IntPtr self,int id,ref Guid iid,uint lcid,ushort flags,ref DISPPARAMS args,IntPtr result,IntPtr exception,IntPtr argerror);
 private Delegate[] roots;private IntPtr table,instance;private uint refs=1;
 public short ReceivedVt;public object Object {get;private set;}
 public NativeVariantDispatch(){
  roots=new Delegate[]{new Query(Q),new Ref(Add),new Ref(Release),new Count(C),new Info(I),new Names(N),new Call(Invoke)};
  table=Marshal.AllocCoTaskMem(IntPtr.Size*7);instance=Marshal.AllocCoTaskMem(IntPtr.Size);
  for(int i=0;i<7;i++)Marshal.WriteIntPtr(table,i*IntPtr.Size,Marshal.GetFunctionPointerForDelegate(roots[i]));
  Marshal.WriteIntPtr(instance,table);Object=Marshal.GetObjectForIUnknown(instance);
 }
 private int Q(IntPtr self,ref Guid iid,out IntPtr obj){
  if(iid==new Guid("00000000-0000-0000-C000-000000000046")||iid==new Guid("00020400-0000-0000-C000-000000000046")){obj=instance;Add(self);return 0;}
  obj=IntPtr.Zero;return unchecked((int)0x80004002);
 }
 private uint Add(IntPtr self){return ++refs;}private uint Release(IntPtr self){if(refs>0)refs--;return refs;}
 private int C(IntPtr self,out uint count){count=0;return 0;}
 private int I(IntPtr self,uint index,uint lcid,out IntPtr info){info=IntPtr.Zero;return unchecked((int)0x80004001);}
 private int N(IntPtr self,ref Guid iid,IntPtr names,uint count,uint lcid,IntPtr ids){
  if(count!=1)return unchecked((int)0x80020006);
  string name=Marshal.PtrToStringUni(Marshal.ReadIntPtr(names));
  if(name!="GetContents")return unchecked((int)0x80020006);
  Marshal.WriteInt32(ids,11);return 0;
 }
 private int Invoke(IntPtr self,int id,ref Guid iid,uint lcid,ushort flags,ref DISPPARAMS args,IntPtr result,IntPtr exception,IntPtr argerror){
  if(id!=11||args.cArgs!=1)return unchecked((int)0x8002000e);
  ReceivedVt=Marshal.ReadInt16(args.rgvarg);
  if(ReceivedVt!=0x400c){if(argerror!=IntPtr.Zero)Marshal.WriteInt32(argerror,0);return unchecked((int)0x80020005);}
  IntPtr inner=Marshal.ReadIntPtr(args.rgvarg,8);
  if(Marshal.ReadInt16(inner)!=8)return unchecked((int)0x80020005);
  VariantClear(inner);Marshal.GetNativeVariantForObject("1\t1.25\t2\t3\r\n",inner);
  if(result!=IntPtr.Zero)Marshal.WriteInt16(result,0);return 0;
 }
 [DllImport("oleaut32.dll")]private static extern int VariantClear(IntPtr value);
 public void Dispose(){
  if(Object!=null){Marshal.FinalReleaseComObject(Object);Object=null;}
  Marshal.FreeCoTaskMem(instance);Marshal.FreeCoTaskMem(table);GC.KeepAlive(roots);
 }
}

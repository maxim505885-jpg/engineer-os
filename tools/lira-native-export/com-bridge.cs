using System;
using System.Globalization;
using System.Reflection;
public static class EngineerLiraComBridge {
 private static object Invoke(object target,string method,object[] args,ParameterModifier[] modifiers) {
  if(target==null) throw new ArgumentNullException("target");
  return target.GetType().InvokeMember(method,
   BindingFlags.Public|BindingFlags.Instance|BindingFlags.InvokeMethod|BindingFlags.OptionalParamBinding,
   null,target,args,modifiers,CultureInfo.InvariantCulture,null);
 }
 public static object CreateTable(object group,int type,string name) {
  // Missing is VT_ERROR/DISP_E_PARAMNOTFOUND, not VT_EMPTY or VT_NULL.
  return Invoke(group,"CreateNewItem",new object[]{type,Missing.Value,0,name,-1},null);
 }
 private static object ReadReference(object table,string method,object initial) {
  object[] args=new object[]{initial};
  ParameterModifier modifier=new ParameterModifier(1);modifier[0]=true;
  Invoke(table,method,args,new ParameterModifier[]{modifier});
  return args[0];
 }
 public static object ReadContents(object table) {return ReadReference(table,"GetContents","");}
 public static object ReadParameters(object table) {return ReadReference(table,"GetParameters",null);}
}

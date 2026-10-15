/* Test-fixture shutdown: never remove data while the spawned process is open. */
async function stopChild(child,{graceMs=2500,killWaitMs=2500}={}){
 if(!child||child.exitCode!==null||child.signalCode!=null)return;
 await new Promise((resolve,reject)=>{
  let forceTimer,deadline;
  const finish=error=>{clearTimeout(forceTimer);clearTimeout(deadline);child.removeListener('close',closed);child.removeListener('error',failed);error?reject(error):resolve();};
  const closed=()=>finish(),failed=error=>finish(error);
  child.once('close',closed);child.once('error',failed);
  forceTimer=setTimeout(()=>{
   deadline=setTimeout(()=>finish(Error('Fixture child did not close after forced shutdown')),killWaitMs);
   child.kill('SIGKILL');
  },graceMs);
  child.kill('SIGINT');
 });
}
module.exports={stopChild};

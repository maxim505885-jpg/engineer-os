"""Launch the supplied Electron runtime with ENGINEER OS; never install services."""
import argparse,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--electron');parser.add_argument('--self-test',action='store_true')
 for name in ('data-dir','state-dir','selection-file'):parser.add_argument('--'+name)
 args=parser.parse_args()
 candidates=[args.electron,os.environ.get('ENGINEER_OS_ELECTRON_EXE'),ROOT/'desktop/node_modules/electron/dist/electron.exe',Path.home()/'Desktop/Платформа для работы ИИ/Платформа СПУ/desktop/node_modules/electron/dist/electron.exe']
 runtime=next((Path(p) for p in candidates if p and Path(p).is_file()),None)
 if not runtime:parser.error('Electron runtime missing: specify --electron or ENGINEER_OS_ELECTRON_EXE')
 command=[str(runtime),str(ROOT/'desktop'),'--python',sys.executable,'--project-dir',str(ROOT)]
 for name in ('data_dir','state_dir','selection_file'):
  value=getattr(args,name)
  if value:command.extend(['--'+name.replace('_','-'),str(Path(value).resolve())])
 if args.self_test:
  if not args.data_dir or not args.state_dir:parser.error('--self-test requires isolated --data-dir and --state-dir')
  command.append('--self-test')
 env=os.environ.copy();env.pop('ELECTRON_RUN_AS_NODE',None)
 process=subprocess.Popen(command,cwd=ROOT,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 return process.wait() if args.self_test else 0
if __name__=='__main__':raise SystemExit(main())

"""Desktop readiness uses existing authenticated runtime identity."""
import json,re,subprocess,sys,tempfile,threading,queue,unittest
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
class SpuDesktopTests(unittest.TestCase):
 def test_desktop_code_is_in_build_identity(self):
  from engineering.local_app.build_identity import BuildIdentity
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'desktop').mkdir();p=root/'desktop/main.js';p.write_text('first')
   first=BuildIdentity(root,discover_git=True);sha=first.report()['source_sha256'];p.write_text('second')
   self.assertNotEqual(sha,BuildIdentity(root,discover_git=True).report()['source_sha256'])
 def test_ready_descriptor_matches_authenticated_build(self):
  with tempfile.TemporaryDirectory() as tmp:
   process=subprocess.Popen([sys.executable,str(ROOT/'scripts/run_local_app.py'),'--no-browser','--port','0','--data-dir',tmp,'--desktop-ready'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
   output=queue.Queue()
   def read():
    for line in process.stdout:output.put(line)
    output.put(None)
   thread=threading.Thread(target=read,daemon=True);thread.start()
   try:
    record=None
    for _ in range(30):
     line=output.get(timeout=10)
     if line is None:break
     if line.startswith('ENGINEER_OS_DESKTOP_READY '):record=json.loads(line.split(' ',1)[1]);break
    self.assertIsNotNone(record,'Owned desktop readiness descriptor missing')
    with urlopen(record['origin']) as response:html=response.read().decode()
    token=re.search(r'name="app-token" content="([^"]+)"',html).group(1)
    with urlopen(Request(record['origin']+'/api/build',headers={'X-Engineer-Token':token})) as response:build=json.load(response)
    self.assertEqual(record['schema'],'ENGINEER_OS_DESKTOP_READY_V1')
    self.assertEqual(record['build']['source_sha256'],build['source_sha256']);self.assertEqual(record['build']['data_root_sha256'],build['data_root_sha256'])
    self.assertFalse(build['acceptance_granted'])
   finally:
    if sys.platform=='win32':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
    else:process.terminate()
    process.wait(timeout=10);thread.join(timeout=2);process.stdout.close()

"""Run against the extracted portable package on a real Windows runner."""
import importlib.util, json, os, sys, tempfile, threading, urllib.request, zipfile
from pathlib import Path
folder=Path(sys.argv[1]).resolve()
os.environ['AAB_WORKBENCH_DATA']=tempfile.mkdtemp(prefix='bundledesk-windows-test-')
spec=importlib.util.spec_from_file_location('server',folder/'app/server.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
assert s.WINDOWS, 'Run this smoke test on Windows'
assert all(s.ENV.values()),s.ENV
for key in ('java','adb','aapt'):assert str(folder) in s.ENV[key],s.ENV
s.run([s.ENV['adb'],'version'])
s.run([s.ENV['aapt'],'version'])
server=s.ThreadingHTTPServer(('127.0.0.1',0),s.Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
def request(path,body=None,extra=None):
 headers={'X-Token':s.TOKEN,**(extra or {})}
 req=urllib.request.Request('http://127.0.0.1:'+str(server.server_port)+path,data=body,headers=headers)
 with urllib.request.urlopen(req) as r:return json.load(r)
try:
 fixture=Path(__file__).parent/'fixture/sample.aab'
 uploaded=request('/api/upload',fixture.read_bytes(),{'X-Filename':'sample.aab','Content-Type':'application/octet-stream'})
 for action in ['inspect','build']:
  job=dict(id=action,logs=[])
  s.execute(job,dict(action=action,aab=uploaded['id'],mode='universal'))
  assert job['state']=='done',job
  assert job['result']['info']['package']=='dev.bundledesk.fixture',job
  if action=='build':
   with zipfile.ZipFile(s.file_for(job['result']['apks'])) as z:
    apk=s.DATA/'universal.apk';apk.write_bytes(z.read('universal.apk'))
   assert s.prepare_apk(apk,s.DATA,job)==apk
 assert not list(s.DATA.rglob('*.secret'))
 print('PASS: Windows bundled tools, HTTP upload, AAB parse, default signing and APKS build')
finally:
 server.shutdown();server.server_close();s.POOL.shutdown(wait=True)
 import shutil
 shutil.rmtree(s.DATA)

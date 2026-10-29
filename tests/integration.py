"""Real bundletool conversion smoke test; uses throwaway fixtures and credentials."""
import importlib.util, os, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ['AAB_WORKBENCH_DATA']=tempfile.mkdtemp(prefix='bundledesk-test-')
spec=importlib.util.spec_from_file_location('server',ROOT/'app/server.py'); s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
with tempfile.TemporaryDirectory() as temp:
 d=Path(temp); sdk=Path.home()/'Library/Android/sdk'
 aapt2=sdk/'build-tools/34.0.0/aapt2'
 s.run([aapt2,'compile','--dir',ROOT/'tests/fixture/res','-o',d/'res.zip'])
 s.run([aapt2,'link','--proto-format','-o',d/'base.apk','-I',sdk/'platforms/android-34/android.jar','--manifest',ROOT/'tests/fixture/AndroidManifest.xml',d/'res.zip'])
 with zipfile.ZipFile(d/'base.apk') as src, zipfile.ZipFile(d/'base.zip','w') as dst:
  for name in src.namelist(): dst.writestr('manifest/AndroidManifest.xml' if name=='AndroidManifest.xml' else name,src.read(name))
 s.bundle('build-bundle','--modules='+str(d/'base.zip'),'--output='+str(d/'fixture.aab'))
 if os.environ.get('BUNDLEDESK_TEST_AAB'):
  import shutil
  shutil.copy2(d/'fixture.aab',os.environ['BUNDLEDESK_TEST_AAB'])
 keytool=str(Path(s.ENV['java']).parent/'keytool')
 # /usr/bin/java is a macOS shim; use discovered JDK home only for test key generation.
 if not Path(keytool).exists(): keytool='keytool'
 s.run([keytool,'-genkeypair','-keystore',d/'fixture.jks','-storepass','fixture-test-only','-keypass','fixture-test-only','-alias','fixture','-dname','CN=Fixture','-keyalg','RSA','-validity','1'])
 payload=dict(action='build',aab=s.register(d/'fixture.aab'),keystore=s.register(d/'fixture.jks'),alias='fixture',storePassword='fixture-test-only',mode='universal')
 job=dict(id='test-convert',logs=[]);s.execute(job,payload)
 assert job['state']=='done',job
 assert 'info' in job['result'],job
 info=job['result']['info'];assert info['package']=='dev.bundledesk.fixture',info
 assert info['label']=='Bundle Desk Test',info
 assert info['versionName']=='1.2.3' and info['versionCode']=='7',info
 assert 'android.permission.INTERNET' in info['permissions'],info
 assert not list(s.DATA.rglob('*.secret'))
 assert Path(s.file_for(job['result']['apks'])).is_file()
 # Parsing and conversion both work without an uploaded keystore or passwords.
 inspect_job=dict(id='inspect-no-key',logs=[])
 s.execute(inspect_job,dict(action='inspect',aab=s.register(d/'fixture.aab')))
 assert inspect_job['state']=='done',inspect_job
 assert not (s.DATA/'default-signing').exists(), 'Parsing must not create a signing key'
 default_job=dict(id='convert-no-key',logs=[])
 s.execute(default_job,dict(action='build',aab=s.register(d/'fixture.aab'),mode='universal'))
 assert default_job['state']=='done',default_job
 assert default_job['result']['info']['package']=='dev.bundledesk.fixture'
 # The default key persists and signs an unsigned APK without touching signed inputs.
 first=s.default_signing();second=s.default_signing();assert first==second
 with zipfile.ZipFile(s.file_for(job['result']['apks'])) as z:
  original=d/'signed.apk';original.write_bytes(z.read('universal.apk'))
 assert s.prepare_apk(original,d,job)==original
 unsigned=d/'unsigned.apk'
 with zipfile.ZipFile(original) as src,zipfile.ZipFile(unsigned,'w') as dst:
  for name in src.namelist():
   if not name.upper().startswith('META-INF/'):dst.writestr(name,src.read(name))
 signed=s.prepare_apk(unsigned,d,job);assert signed.exists()
 assert s.apk_info(signed,d,job)['package']=='dev.bundledesk.fixture'
 artifact_job=dict(id='inspect-existing',logs=[])
 s.execute(artifact_job,dict(action='inspect-artifact',apks=s.register(original)))
 assert artifact_job['state']=='done',artifact_job
 assert artifact_job['result']['info']['package']=='dev.bundledesk.fixture'
 bad=dict(id='test-device',logs=[]);s.execute(bad,dict(action='install',device='nonexistent'))
 assert bad['state']=='error' and '设备' in bad['error']
 print('PASS: real AAB → signed APKS; metadata; password cleanup; default-signing reuse; unsigned APK signing; signed APK preservation; APK inspection; missing-device rejection')

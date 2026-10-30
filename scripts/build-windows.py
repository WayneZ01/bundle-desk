#!/usr/bin/env python3
"""Build Windows x64 portable ZIP on macOS, Linux or Windows (Python 3.9+)."""
import argparse, concurrent.futures, hashlib, json, shutil, subprocess, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.runtime-cache/windows'
SOURCES={
 'python':'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip',
 'jre':'https://cdn.azul.com/zulu/bin/zulu17.70.113-ca-jre17.0.21.0.3-win_x64.zip',
 'platform-tools':'https://dl.google.com/android/repository/platform-tools-latest-windows.zip',
 'build-tools':'https://dl.google.com/android/repository/build-tools_r34-windows.zip',
}
def download(item):
 name,url=item; path=CACHE/(name+'.zip')
 if not path.exists() or not zipfile.is_zipfile(path):
  partial=path.with_suffix('.partial')
  subprocess.run(['curl','--http1.1','-fL','--retry','2','--connect-timeout','20','--max-time','900',url,'-o',str(partial)],check=True)
  if not zipfile.is_zipfile(partial): raise ValueError('下载文件不是完整 ZIP: '+name)
  partial.replace(path)
 with zipfile.ZipFile(path) as z:
  bad=z.testzip()
  if bad: raise ValueError('ZIP 校验失败: '+bad)
 return name,dict(url=url,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def build():
 CACHE.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: manifest=dict(pool.map(download,SOURCES.items()))
 out=ROOT/'dist/Bundle Desk Windows x64'
 if out.exists(): shutil.rmtree(out)
 app=out/'app';app.mkdir(parents=True)
 for name in ['server.py','bundletool.jar','apksigner.jar']:shutil.copy2(ROOT/'app'/name,app/name)
 shutil.copytree(ROOT/'app/web',app/'web')
 rt=out/'runtime/windows-x86_64';rt.mkdir(parents=True)
 with zipfile.ZipFile(CACHE/'python.zip') as z:z.extractall(rt/'python')
 with tempfile.TemporaryDirectory() as temp:
  with zipfile.ZipFile(CACHE/'jre.zip') as z:z.extractall(temp)
  source=next(p.parent for p in Path(temp).rglob('bin') if (p/'java.exe').exists())
  shutil.copytree(source,rt/'jre')
 tools=rt/'tools';tools.mkdir()
 for name in ['platform-tools','build-tools']:
  with zipfile.ZipFile(CACHE/(name+'.zip')) as z:
   # The aapt/adb executables and their adjacent DLLs; preserve vendor NOTICE.
   exe='adb.exe' if name=='platform-tools' else 'aapt.exe'
   entry=next(n for n in z.namelist() if n.endswith('/'+exe));prefix=entry.rsplit('/',1)[0]+'/'
   for n in z.namelist():
    relative=n.removeprefix(prefix)
    if n.startswith(prefix) and '/' not in relative and (relative.lower().endswith('.dll') or relative==exe or relative=='NOTICE.txt'):
     target=tools/('NOTICE-'+name+'.txt' if relative=='NOTICE.txt' else relative)
     target.write_bytes(z.read(n))
 for source in (ROOT/'windows').iterdir():
  if source.is_file():shutil.copy2(source,out/source.name)
 for name in ['LICENSE','THIRD_PARTY_NOTICES.md']:
  if (ROOT/name).exists():shutil.copy2(ROOT/name,out/name)
 if (ROOT/'docs/legal').exists():shutil.copytree(ROOT/'docs/legal',out/'docs/legal')
 icon=ROOT/'mac/assets/BundleDesk.ico'
 if icon.exists():shutil.copy2(icon,out/'BundleDesk.ico')
 (out/'runtime-sources.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 required=['python/python.exe','python/python312.dll','python/python312.zip','jre/bin/java.exe','jre/bin/keytool.exe','tools/adb.exe','tools/AdbWinApi.dll','tools/AdbWinUsbApi.dll','tools/aapt.exe']
 for name in required:
  if not (rt/name).is_file():raise ValueError('缺少运行依赖: '+name)
 archive=ROOT/'dist/Bundle Desk Windows x64.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for path in out.rglob('*'):
   if path.is_file():z.write(path,str(path.relative_to(out.parent)))
 html_archive=ROOT/'dist/Bundle Desk HTML Windows x64.zip'
 with zipfile.ZipFile(html_archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for path in out.rglob('*'):
   if path.is_file():z.write(path,str(Path('Bundle Desk HTML Windows x64')/path.relative_to(out)))
 print('Windows portable package:',archive)
 print('Windows HTML local package:',html_archive)
if __name__=='__main__':build()

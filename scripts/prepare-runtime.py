#!/usr/bin/env python3
"""Build-time dependency preparation; end users never run this script."""
import concurrent.futures, hashlib, json, os, shutil, subprocess, tarfile, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; RUNTIME=ROOT/'runtime'; CACHE=ROOT/'.runtime-cache'; CACHE.mkdir(exist_ok=True)
SOURCES={}
for arch,pyarch,jarch in [('arm64','aarch64','aarch64'),('x86_64','x86_64','x64')]:
 SOURCES['python-'+arch]=f'https://github.com/astral-sh/python-build-standalone/releases/download/20261026/cpython-3.12.16%2B20261026-{pyarch}-apple-darwin-install_only_stripped.tar.gz'
 SOURCES['jre-'+arch]=f'https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.21%2B9/OpenJDK17U-jre_{jarch}_mac_hotspot_17.0.21_9.tar.gz'
SOURCES['platform-tools']='https://dl.google.com/android/repository/platform-tools-latest-darwin.zip'
SOURCES['build-tools']='https://dl.google.com/android/repository/build-tools_r34-macosx.zip'
def prepare(pair):
 name,url=pair; target=CACHE/(name+('.zip' if name.endswith('tools') else '.tar.gz'))
 if not target.exists():
  partial=target.with_suffix('.partial')
  subprocess.run(['curl','--http1.1','-fL','--retry','3','--connect-timeout','20','--max-time','900',url,'-o',str(partial)],check=True); partial.rename(target)
 record=dict(url=url,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
 if name.startswith(('python-','jre-')):
  kind,arch=name.split('-',1); dest=RUNTIME/arch;dest.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory() as temp:
   with tarfile.open(target) as archive: archive.extractall(temp,filter='data')
   source=next(Path(temp).iterdir()); final=dest/kind
   if final.exists(): shutil.rmtree(final)
   shutil.copytree(source,final,symlinks=True)
 else:
  with tempfile.TemporaryDirectory() as temp:
   with zipfile.ZipFile(target) as archive: archive.extractall(temp)
   base=next(Path(temp).iterdir()); out=RUNTIME/'tools';out.mkdir(parents=True,exist_ok=True)
   names=['adb','NOTICE.txt'] if name=='platform-tools' else ['aapt','lib64','NOTICE.txt']
   for n in names:
    src=base/n;dst=out/('NOTICE-'+name+'.txt' if n=='NOTICE.txt' else n)
    if src.is_dir(): shutil.copytree(src,dst,dirs_exist_ok=True)
    else: shutil.copy2(src,dst)
   (out/('adb' if name=='platform-tools' else 'aapt')).chmod(0o755)
 return name,record
if __name__=='__main__':
 # Python 3.12+ supplies tar extraction filtering. Only the build machine needs it.
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: manifest=dict(pool.map(prepare,SOURCES.items()))
 (RUNTIME/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Runtime prepared:',RUNTIME)

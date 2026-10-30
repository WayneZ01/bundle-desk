#!/usr/bin/env python3
"""Build self-contained Windows desktop EXE and bundled Fixed WebView2 on Windows."""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
URL='https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/876df7fd-c9c1-4feb-8a51-a768caada6dd/Microsoft.WebView2.FixedVersionRuntime.156.0.4314.56.x64.cab'
def build(skip_base=False):
 if os.name!='nt': raise SystemExit('Native EXE packaging requires Windows. Use the Windows GitHub Actions workflow.')
 if not skip_base:subprocess.run([sys.executable,str(ROOT/'scripts/build-windows.py')],check=True)
 base=ROOT/'dist/Bundle Desk Windows x64';out=ROOT/'dist/Bundle Desk EXE Windows x64'
 if out.exists():shutil.rmtree(out)
 shutil.copytree(base,out)
 native=ROOT/'dist/windows-native-launcher'
 subprocess.run(['dotnet','publish',str(ROOT/'windows/native/BundleDesk.csproj'),'-c','Release','-r','win-x64','--self-contained','true','-o',str(native)],check=True)
 for path in native.iterdir():
  if path.is_file():shutil.copy2(path,out/path.name)
  elif path.is_dir():shutil.copytree(path,out/path.name,dirs_exist_ok=True)
 cache=ROOT/'.runtime-cache/windows';cache.mkdir(parents=True,exist_ok=True)
 cab=cache/'webview2-156.0.4314.56-x64.cab'
 if not cab.exists():
  partial=cab.with_suffix('.partial');subprocess.run(['curl','-fL','--retry','3','--max-time','900',URL,'-o',str(partial)],check=True);partial.replace(cab)
 if cab.read_bytes()[:4]!=b'MSCF':raise ValueError('Invalid Microsoft Fixed WebView2 CAB')
 with tempfile.TemporaryDirectory() as temp:
  subprocess.run(['expand.exe',str(cab),'-F:*',temp],check=True,stdout=subprocess.DEVNULL)
  browser=next(Path(temp).rglob('msedgewebview2.exe')).parent
  shutil.copytree(browser,out/'runtime/webview2')
 manifest=json.loads((out/'runtime-sources.json').read_text())
 manifest['webview2']={'url':URL,'sha256':hashlib.sha256(cab.read_bytes()).hexdigest(),'version':'156.0.4314.56'}
 (out/'runtime-sources.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 (out/'EXE 使用说明.txt').write_text('Windows EXE 应用版：完整解压后双击 BundleDesk.exe，在独立窗口使用。关闭应用会停止本地服务。\n已内置 .NET、Fixed WebView2、Python、Java 与 Android 工具，请保留整个目录。\n如需使用系统浏览器，也可双击同包的“启动 HTML 版.cmd”。\n本应用尚未进行 Windows 代码签名。数据与签名目录沿用 %LOCALAPPDATA%\\Bundle Desk。\n',encoding='utf-8')
 archive=ROOT/'dist/Bundle Desk EXE Windows x64.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in out.rglob('*'):
   if p.is_file():z.write(p,str(p.relative_to(out.parent)))
 print('Windows EXE package:',archive)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--skip-base',action='store_true');args=parser.parse_args();build(args.skip_base)

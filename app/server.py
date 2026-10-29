#!/usr/bin/env python3
"""Local-only Android bundle workbench. No third-party Python dependencies."""
import platform
import argparse, concurrent.futures, hashlib, json, mimetypes, os, re, secrets, shutil, subprocess, tempfile, threading, time, webbrowser, zipfile
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT.parent / 'runtime'
WINDOWS = os.name == 'nt'
EXE = '.exe' if WINDOWS else ''
ARCH = 'windows-x86_64' if WINDOWS else ('arm64' if platform.machine() == 'arm64' else 'x86_64')
PROCESS_OPTIONS = {'creationflags': subprocess.CREATE_NO_WINDOW} if WINDOWS else {}
BUNDLED = RUNTIME / ARCH
DEFAULT_DATA = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'Bundle Desk' if WINDOWS else Path.home() / 'Library/Application Support/AAB Workbench'
DATA = Path(os.environ.get('AAB_WORKBENCH_DATA', DEFAULT_DATA))
DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
TOKEN = secrets.token_urlsafe(32)
FILES, JOBS = {}, {}
POOL = concurrent.futures.ThreadPoolExecutor(max_workers=1)
LOCK = threading.Lock()

def locate(name, candidates=()):
    for p in [os.environ.get(name.upper() + '_BIN', ''), *candidates, shutil.which(name)]:
        if p and Path(p).is_file() and os.access(p, os.X_OK): return str(p)
    return None

def discover():
    sdk = Path(os.environ.get('ANDROID_HOME', Path.home() / ('AppData/Local/Android/Sdk' if WINDOWS else 'Library/Android/sdk')))
    tools = BUNDLED / 'tools' if WINDOWS else RUNTIME / 'tools'
    bundled_java = BUNDLED / ('jre/bin/java.exe' if WINDOWS else 'jre/Contents/Home/bin/java')
    java = None
    for p in filter(None, [str(bundled_java), os.environ.get('JAVA_BIN'), '/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin/java', '/opt/homebrew/opt/openjdk/bin/java', shutil.which('java')]):
        try:
            v = subprocess.run([p, '-version'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=8, **PROCESS_OPTIONS).stderr
            m = re.search(r'version "(\d+)(?:\.(\d+))?', v)
            if m and (int(m[2]) if m[1] == '1' else int(m[1])) >= 11: java = p; break
        except (OSError, subprocess.TimeoutExpired): pass
    builds = sorted((sdk / 'build-tools').glob('*'), key=lambda p: [int(x) for x in re.findall(r'\d+', p.name)], reverse=True)
    jar = Path(os.environ.get('BUNDLETOOL_JAR', ROOT / 'bundletool.jar'))
    return dict(java=java, adb=locate('adb', [tools / ('adb'+EXE), sdk / ('platform-tools/adb'+EXE), '/opt/homebrew/bin/adb']), aapt=locate('aapt', [tools / ('aapt'+EXE)] + [p / ('aapt'+EXE) for p in builds]), bundletool=str(jar) if jar.is_file() else None)
ENV = discover()

def run(args, job=None, timeout=600):
    # Never print command arguments: signing secrets are intentionally excluded from logs.
    proc = subprocess.Popen([str(x) for x in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', **PROCESS_OPTIONS)
    try:
        output, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill(); proc.communicate(); raise ValueError('执行超时，请检查设备和工具环境')
    if job:
        with LOCK: job['logs'].append(output[-24000:])
    if proc.returncode: raise ValueError(output[-6000:] or '命令执行失败')
    return output

def bundle(*args, job=None):
    if not ENV['java'] or not ENV['bundletool']: raise ValueError('需要 Java 11+ 和 bundletool.jar')
    return run([ENV['java'], '-jar', ENV['bundletool'], *args], job)

def devices():
    if not ENV['adb']: return []
    out = run([ENV['adb'], 'devices', '-l'], timeout=20)
    result = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and not line.startswith('*'):
            result.append(dict(id=parts[0], state=parts[1], description=' '.join(parts[2:])))
    return result

def device(serial):
    if not serial or not any(x['id'] == serial and x['state'] == 'device' for x in devices()):
        raise ValueError('请选择已授权且在线的设备，或刷新设备列表')
    return serial

def file_for(key, suffix=None):
    item = FILES.get(key)
    if not item or (suffix and item.suffix.lower() != suffix): raise ValueError('文件不存在或类型不匹配，请重新上传')
    return item

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

A = '{http://schemas.android.com/apk/res/android}'
def manifest_info(xml):
    root = ET.fromstring(xml)
    app = root.find('application')
    return dict(package=root.get('package'), versionName=root.get(A+'versionName'), versionCode=root.get(A+'versionCode'),
        sdk=[{k.replace(A, ''): v for k,v in e.attrib.items()} for e in root.findall('uses-sdk')],
        permissions=[e.get(A+'name') for e in root if e.tag.startswith('uses-permission')],
        features=[dict(e.attrib) for e in root.findall('uses-feature')],
        application={k.replace(A,''): v for k,v in app.attrib.items()} if app is not None else {},
        components=[dict(type=e.tag, **{k.replace(A,''):v for k,v in e.attrib.items()}) for e in app] if app is not None else [], manifest=xml)

def inspect(aab, directory, job, apks=None):
    xml = bundle('dump', 'manifest', '--bundle='+str(aab), '--module=base', job=job)
    info = manifest_info(xml)
    info.update(size=aab.stat().st_size, sha256=digest(aab), modules=[], nativeLibraries=[])
    with zipfile.ZipFile(aab) as z:
        info['modules'] = sorted({n.split('/')[0] for n in z.namelist() if '/manifest/AndroidManifest.xml' in n})
        info['nativeLibraries'] = [n for n in z.namelist() if '/lib/' in n and n.endswith('.so')]
    if apks and ENV['aapt']:
        with zipfile.ZipFile(apks) as z:
            names = z.namelist()
            name = next((n for n in names if n == 'universal.apk'), None) or next((n for n in names if n.endswith('base-master.apk')), None) or next((n for n in names if n.endswith('.apk')), None)
            if name:
                apk = directory / 'inspect.apk'
                with z.open(name) as src, apk.open('wb') as dst: shutil.copyfileobj(src, dst)
                badging = run([ENV['aapt'], 'dump', 'badging', apk], job)
                info['badging'] = badging
                for key, pattern in [('label', r"application-label:'([^']*)'"), ('launchableActivity', r"launchable-activity: name='([^']*)'"), ('minSdk', r"sdkVersion:'([^']*)'"), ('targetSdk', r"targetSdkVersion:'([^']*)'")]:
                    m = re.search(pattern, badging)
                    if m: info[key] = m[1]
                icons = re.findall(r"application-icon-\d+:'([^']+)'", badging)
                with zipfile.ZipFile(apk) as az:
                    for icon in reversed(icons):
                        if icon.endswith(('.png','.webp','.jpg')) and icon in az.namelist():
                            dest = directory / ('icon'+Path(icon).suffix); dest.write_bytes(az.read(icon))
                            info['icon'] = '/download/'+register(dest); break
                info['abis'] = re.findall(r"native-code: (.*)", badging)
    return info

def default_signing(job=None):
    folder = DATA / 'default-signing'; folder.mkdir(mode=0o700, exist_ok=True)
    password_file = folder / 'password'
    if not password_file.exists():
        password_file.touch(mode=0o600); password_file.write_text(secrets.token_urlsafe(24)+'\n')
    password = password_file.read_text().strip()
    ks = folder / 'test.jks'
    if not ks.exists():
        if not ENV['java']: raise ValueError('缺少 Java 运行时')
        keytool = Path(ENV['java']).parent / ('keytool'+EXE)
        if not keytool.exists(): keytool = Path(shutil.which('keytool') or '')
        run([keytool, '-genkeypair', '-keystore', ks, '-storetype', 'JKS', '-storepass:file', password_file, '-keypass:file', password_file, '-alias', 'bundledesk-test', '-dname', 'CN=Bundle Desk Local Test', '-keyalg', 'RSA', '-validity', '36500'], job)
    return ks, 'bundledesk-test', password

def apk_info(apk, directory, job):
    if not ENV['aapt']: raise ValueError('缺少 APK 解析工具')
    text = run([ENV['aapt'], 'dump', 'badging', apk], job)
    info = dict(size=apk.stat().st_size, sha256=digest(apk), badging=text, permissions=re.findall(r"uses-permission(?:-sdk-\d+)?: name='([^']+)'", text))
    for key, pattern in [('package',r"package: name='([^']*)'"),('versionName',r"versionName='([^']*)'"),('versionCode',r"versionCode='([^']*)'"),('label',r"application-label:'([^']*)'"),('minSdk',r"sdkVersion:'([^']*)'"),('targetSdk',r"targetSdkVersion:'([^']*)'"),('launchableActivity',r"launchable-activity: name='([^']*)'")]:
        m=re.search(pattern,text)
        if m: info[key]=m[1]
    with zipfile.ZipFile(apk) as z:
        info['nativeLibraries']=[n for n in z.namelist() if n.startswith('lib/') and n.endswith('.so')]
        for name in reversed(re.findall(r"application-icon-\d+:'([^']+)'",text)):
            if name.endswith(('.png','.webp','.jpg')) and name in z.namelist():
                path=directory/('icon'+Path(name).suffix);path.write_bytes(z.read(name));info['icon']='/download/'+register(path);break
    info['manifestTree']=run([ENV['aapt'],'dump','xmltree',apk,'AndroidManifest.xml'],job)
    return info

def prepare_apk(apk, directory, job):
    signer = ROOT / 'apksigner.jar'
    if not signer.exists(): raise ValueError('缺少内置 apksigner.jar')
    command=[ENV['java'],'-jar',str(signer)]
    check=subprocess.run(command+['verify',str(apk)],capture_output=True,text=True,encoding='utf-8',errors='replace',**PROCESS_OPTIONS)
    if check.returncode == 0:
        job['logs'].append('APK 已有有效签名，保留原签名。'); return apk
    # Refuse damaged or incompatible signed APKs instead of silently replacing their certificates.
    with zipfile.ZipFile(apk) as z:
        v1=any(n.upper().startswith('META-INF/') and n.upper().endswith(('.RSA','.DSA','.EC')) for n in z.namelist())
    with apk.open('rb') as f:
        signed_block=False; tail=b''
        for block in iter(lambda:f.read(1024*1024),b''):
            chunk=tail+block
            if b'APK Sig Block 42' in chunk: signed_block=True;break
            tail=chunk[-32:]
    if v1 or signed_block: raise ValueError('APK 包含签名但校验失败，未自动覆盖原签名：'+check.stderr[-2000:])
    ks,alias,password=default_signing(job)
    pw=directory/'apk-password.secret';pw.touch(mode=0o600);pw.write_text(password+'\n'+password+'\n')
    output=directory/'signed.apk'
    try:
        run(command+['sign','--ks',str(ks),'--ks-key-alias',alias,'--ks-pass','file:'+str(pw),'--key-pass','file:'+str(pw),'--out',str(output),str(apk)],job)
        run(command+['verify',str(output)],job)
    finally: pw.unlink(missing_ok=True)
    job['logs'].append('未签名 APK 已使用本机默认测试签名。')
    return output

def register(path):
    key = secrets.token_hex(16); FILES[key] = path; return key

def execute(job, payload):
    job['state'] = 'running'
    try:
        action = payload['action']
        if action in ('build','inspect'):
            aab = file_for(payload.get('aab'), '.aab')
            directory = DATA / job['id']; directory.mkdir(mode=0o700)
            apks = directory / (aab.stem + '.apks')
            if action == 'build':
                if payload.get('keystore'):
                    ks = file_for(payload.get('keystore'))
                    alias = payload.get('alias', '').strip()
                else:
                    ks, alias, password = default_signing(job)
                    payload['storePassword'] = password; payload['keyPassword'] = password
                    job['logs'].append('使用本机默认测试签名。')
                if not alias: raise ValueError('请输入签名别名')
                args = ['build-apks', '--bundle='+str(aab), '--output='+str(apks), '--ks='+str(ks), '--ks-key-alias='+alias, '--overwrite']
                # bundletool supports file: passwords; private temporary files avoid process-list disclosure.
                try:
                    for field, flag in [('storePassword','--ks-pass='), ('keyPassword','--key-pass=')]:
                        pw = payload.get(field) or payload.get('storePassword', '')
                        p = directory / (field+'.secret'); p.touch(mode=0o600); p.write_text(pw+'\n')
                        args.append(flag+'file:'+str(p))
                    if payload.get('mode') == 'device': args += ['--connected-device', '--device-id='+device(payload.get('device')), '--adb='+ENV['adb']]
                    else: args += ['--mode=universal']
                    bundle(*args, job=job)
                finally:
                    for p in directory.glob('*.secret'): p.unlink(missing_ok=True)
                job['result'] = dict(apks=register(apks), name=apks.name, device=payload.get('device') if payload.get('mode') == 'device' else None)
            else: job['result'] = {}
            # Conversion remains downloadable if optional metadata extraction fails.
            try: job['result']['info'] = inspect(aab, directory, job, apks if apks.exists() else None)
            except Exception as exc:
                if action == 'inspect': raise
                job['result']['infoError'] = str(exc)
        elif action == 'inspect-artifact':
            source = file_for(payload.get('apks'))
            directory = DATA / job['id']; directory.mkdir(mode=0o700)
            apk = source
            if source.suffix.lower() == '.apks':
                with zipfile.ZipFile(source) as z:
                    name = next((n for n in z.namelist() if n == 'universal.apk' or n.endswith('base-master.apk')), None) or next((n for n in z.namelist() if n.endswith('.apk')), None)
                    if not name: raise ValueError('APKS 中没有 APK')
                    apk = directory / 'base.apk'
                    with z.open(name) as src, apk.open('wb') as dst: shutil.copyfileobj(src,dst)
            job['result'] = {'info':apk_info(apk,directory,job)}
        elif action in ('install','launch'):
            serial = device(payload.get('device'))
            if action == 'install':
                apks = file_for(payload.get('apks'))
                directory = DATA / job['id']; directory.mkdir(mode=0o700)
                if apks.suffix.lower() == '.apk':
                    signed = prepare_apk(apks,directory,job)
                    run([ENV['adb'],'-s',serial,'install','-r',signed],job)
                elif apks.suffix.lower() == '.apks':
                    bundle('install-apks', '--apks='+str(apks), '--device-id='+serial, '--adb='+ENV['adb'], job=job)
                else: raise ValueError('请选择 APK 或 APKS')
            else:
                package = payload.get('package', '')
                if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+', package): raise ValueError('缺少有效包名，请先查看应用信息')
                output = run([ENV['adb'], '-s', serial, 'shell', 'monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1'], job, timeout=30)
                if 'Events injected: 1' not in output: raise ValueError('未成功启动，应用可能没有启动入口：'+output)
            job['result'] = {'message':'安装完成' if action == 'install' else '已启动应用'}
        else: raise ValueError('不支持的操作')
        job['state'] = 'done'
    except Exception as exc:
        job['state'] = 'error'; job['error'] = str(exc)
    finally:
        payload.clear()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def send(self, status, body, mime='application/json'):
        if not isinstance(body, bytes): body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type', mime); self.send_header('Content-Length', str(len(body))); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(body)
    def allowed(self):
        return self.headers.get('Host') == '127.0.0.1:'+str(self.server.server_port)
    def do_GET(self):
        if not self.allowed(): return self.send(403, {'error':'Invalid host'})
        path = self.path.split('?')[0]
        if path in ('/','/app.js','/style.css'):
            p = ROOT / 'web' / ('index.html' if path == '/' else path[1:])
            return self.send(200, p.read_bytes(), mimetypes.guess_type(str(p))[0] or 'text/plain')
        if self.headers.get('X-Token') != TOKEN: return self.send(403, {'error':'请从启动器打开工具'})
        try:
            if path == '/api/status': return self.send(200, dict(environment=ENV, devices=devices(), dataDirectory=str(DATA)))
            if path.startswith('/api/jobs/'):
                j = JOBS.get(path.rsplit('/',1)[-1]); return self.send(200 if j else 404, j or {'error':'任务不存在'})
            if path.startswith('/download/'):
                p = file_for(path.rsplit('/',1)[-1])
                self.send_response(200); self.send_header('Content-Type', mimetypes.guess_type(str(p))[0] or 'application/octet-stream'); self.send_header('Content-Length',str(p.stat().st_size)); self.send_header('Cache-Control','no-store'); self.end_headers()
                with p.open('rb') as f: shutil.copyfileobj(f, self.wfile)
                return
            return self.send(404, {'error':'Not found'})
        except Exception as exc: self.send(400, {'error':str(exc)})
    def do_POST(self):
        if not self.allowed() or self.headers.get('X-Token') != TOKEN: return self.send(403, {'error':'Invalid session'})
        try:
            size = int(self.headers.get('Content-Length','0'))
            if size <= 0 or size > 4*1024**3: raise ValueError('文件为空或超过 4 GB')
            if self.path == '/api/upload':
                name = Path(self.headers.get('X-Filename','upload')).name
                # Filename is encoded by the browser; only its extension is trusted.
                from urllib.parse import unquote
                name = Path(unquote(name)).name
                if Path(name).suffix.lower() not in ('.aab','.jks','.keystore','.p12','.pfx','.apks','.apk'): raise ValueError('不支持的文件类型')
                folder = DATA / secrets.token_hex(16); folder.mkdir(mode=0o700); path = folder / name
                try:
                    with path.open('wb') as f:
                        remaining = size
                        while remaining:
                            block = self.rfile.read(min(1024*1024, remaining))
                            if not block: raise ValueError('上传中断')
                            f.write(block); remaining -= len(block)
                    return self.send(200, {'id':register(path), 'name':name})
                except Exception:
                    path.unlink(missing_ok=True); raise
            if self.path == '/api/clear':
                if any(j['state'] in ('queued', 'running') for j in JOBS.values()): raise ValueError('请等待任务结束后清理')
                folders = {p.parent for p in FILES.values()} | {DATA / key for key in JOBS}
                for folder in folders:
                    if folder.parent == DATA: shutil.rmtree(folder, ignore_errors=True)
                FILES.clear(); JOBS.clear()
                return self.send(200, {'message':'本次会话文件已清理'})
            if self.path != '/api/jobs' or size > 65536: raise ValueError('无效请求')
            payload = json.loads(self.rfile.read(size)); key = secrets.token_hex(16)
            job = dict(id=key, state='queued', logs=[]); JOBS[key] = job
            POOL.submit(execute, job, payload); self.send(202, job)
        except Exception as exc: self.send(400, {'error':str(exc)})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--port', type=int, default=0); parser.add_argument('--no-browser', action='store_true'); args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    url = 'http://127.0.0.1:'+str(server.server_port)+'/#'+TOKEN
    print(url, flush=True)
    if not args.no_browser: webbrowser.open(url)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close(); POOL.shutdown(wait=True)

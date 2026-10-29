import importlib.util, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('server',ROOT/'app/server.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class WindowsPaths(unittest.TestCase):
 def test_bundled_windows_tools_take_priority(self):
  with tempfile.TemporaryDirectory(prefix='Bundle Desk 中文 ') as folder:
   base=Path(folder);rt=base/'runtime/windows-x86_64'
   for relative in ['jre/bin/java.exe','tools/adb.exe','tools/aapt.exe']:
    file=rt/relative;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(b'MZ');file.chmod(0o755)
   with patch.multiple(s,WINDOWS=True,EXE='.exe',BUNDLED=rt),patch.object(s.subprocess,'run',return_value=type('Result',(),{'stderr':'openjdk version "17.0.21"'})()):
    env=s.discover()
   self.assertEqual(env['java'],str(rt/'jre/bin/java.exe'))
   self.assertEqual(env['adb'],str(rt/'tools/adb.exe'))
   self.assertEqual(env['aapt'],str(rt/'tools/aapt.exe'))
if __name__=='__main__':unittest.main()

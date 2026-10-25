import os, subprocess, sys, tempfile, unittest, sqlite3, importlib.util
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

class Deployment(unittest.TestCase):
    def test_private_bootstrap_creates_admin_and_guides_once(self):
        import app
        spec=importlib.util.spec_from_file_location('create_admin',ROOT/'scripts/create_admin.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        original=app.DATA
        with tempfile.TemporaryDirectory() as tmp:
            try:
                app.DATA=Path(tmp)
                with patch('builtins.input',side_effect=['Admin VPS','admin@example.test']),patch('getpass.getpass',return_value='test-password-123'),patch('builtins.print'):
                    module.main()
                    module.main()
                with app.db() as c:
                    self.assertEqual(c.execute("SELECT count(*) FROM users WHERE role='admin'").fetchone()[0],1)
                    self.assertEqual(c.execute("SELECT count(*) FROM entries WHERE guide_key IS NOT NULL").fetchone()[0],30)
                    user=c.execute('SELECT * FROM users').fetchone()
                    self.assertEqual(user['password'],app.password('test-password-123',user['salt']))
            finally:app.DATA=original

    def test_production_setup_endpoint_closed(self):
        import urllib.request,urllib.error,json,socket,time
        with tempfile.TemporaryDirectory() as tmp:
            with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
            p=subprocess.Popen([sys.executable,'app.py'],cwd=ROOT,env={**os.environ,'PORT':str(port),'DATA_DIR':tmp,'ALLOW_SETUP':'0'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                url=f'http://127.0.0.1:{port}'
                for _ in range(80):
                    try:
                        with urllib.request.urlopen(url+'/api/state') as r:self.assertFalse(json.load(r)['setup'])
                        break
                    except OSError:time.sleep(.1)
                else:self.fail('Servidor não iniciou')
                request=urllib.request.Request(url+'/api/setup',data=json.dumps({'name':'Intruso','email':'x@x.test','password':'abcdefgh'}).encode(),headers={'Content-Type':'application/json'})
                with self.assertRaises(urllib.error.HTTPError) as ex:urllib.request.urlopen(request)
                self.assertEqual(ex.exception.code,403)
                c=sqlite3.connect(Path(tmp)/'plantrip.db')
                try:self.assertEqual(c.execute('SELECT count(*) FROM users').fetchone()[0],0)
                finally:c.close()
            finally:p.terminate();p.wait()

if __name__=='__main__':unittest.main()

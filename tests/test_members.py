import importlib.util,tempfile,unittest
from pathlib import Path
import app

class CompanionPasswords(unittest.TestCase):
    def test_reset_is_explicit_and_revokes_only_target_sessions(self):
        spec=importlib.util.spec_from_file_location('import_members',Path(__file__).resolve().parents[1]/'scripts/import_members.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        original=app.DATA
        with tempfile.TemporaryDirectory() as tmp:
            try:
                app.DATA=Path(tmp);app.init()
                record={'name':'Teste','email':'member@example.test','password':'initial123'}
                self.assertEqual(module.import_members([record],'Europa'),(1,1))
                with app.db() as c:
                    uid=c.execute('SELECT id FROM users WHERE email=?',(record['email'],)).fetchone()[0]
                    c.execute("INSERT INTO sessions VALUES('test-session',?,'9999-01-01')",(uid,))
                changed={**record,'password':'replacement987'}
                module.import_members([changed],'Europa')
                with app.db() as c:
                    user=c.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
                    self.assertEqual(user['password'],app.password(record['password'],user['salt']))
                module.import_members([changed],'Europa',reset_passwords=True)
                with app.db() as c:
                    user=c.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
                    self.assertEqual(user['password'],app.password(changed['password'],user['salt']))
                    self.assertEqual(c.execute('SELECT count(*) FROM sessions WHERE user_id=?',(uid,)).fetchone()[0],0)
                    self.assertEqual(c.execute('SELECT count(*) FROM users').fetchone()[0],1)
                    self.assertEqual(c.execute('SELECT count(*) FROM trip_members WHERE user_id=?',(uid,)).fetchone()[0],1)
            finally:app.DATA=original

if __name__=='__main__':unittest.main()

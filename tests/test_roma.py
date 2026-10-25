import sqlite3, unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from roma2026 import apply,apply_file,MARKER

class RomeMigration(unittest.TestCase):
    def test_preserves_memories_and_runs_once(self):
        c=sqlite3.connect(':memory:')
        try:
            c.executescript('''CREATE TABLE migrations(name TEXT PRIMARY KEY);
            CREATE TABLE trips(id INTEGER,name TEXT,start TEXT);
            CREATE TABLE users(id INTEGER,role TEXT);
            CREATE TABLE entries(id INTEGER PRIMARY KEY,kind TEXT,title TEXT,place TEXT,start TEXT,end TEXT,description TEXT,category TEXT,user_id INTEGER,trip_id INTEGER,guide_key TEXT,sort_order INTEGER,attraction_id INTEGER);
            INSERT INTO trips VALUES(1,'Europa','2026-10-27');
            INSERT INTO users VALUES(1,'admin');
            INSERT INTO entries(id,kind,title,description,trip_id,guide_key) VALUES(10,'tour','Coliseu, Fórum Romano e Palatino','Nota personalizada',1,'roma-coliseu');
            INSERT INTO entries(id,kind,title,trip_id,attraction_id) VALUES(11,'diary','Nossa memória',1,10);''')
            apply(c)
            self.assertEqual(c.execute('SELECT start FROM entries WHERE id=10').fetchone()[0],'2026-10-31T09:00')
            self.assertIn('Nota personalizada',c.execute('SELECT description FROM entries WHERE id=10').fetchone()[0])
            self.assertEqual(c.execute('SELECT attraction_id FROM entries WHERE id=11').fetchone()[0],10)
            count=c.execute('SELECT count(*) FROM entries').fetchone()[0]
            c.execute("UPDATE entries SET title='Nova edição do admin' WHERE id=10")
            apply(c)
            self.assertEqual(c.execute('SELECT count(*) FROM entries').fetchone()[0],count)
            self.assertEqual(c.execute('SELECT title FROM entries WHERE id=10').fetchone()[0],'Nova edição do admin')
        finally:c.close()

    def test_paris_keeps_arrival_and_existing_memories(self):
        c=sqlite3.connect(':memory:')
        try:
            c.executescript('''CREATE TABLE migrations(name TEXT PRIMARY KEY);
            CREATE TABLE trips(id INTEGER,name TEXT,start TEXT);
            CREATE TABLE users(id INTEGER,role TEXT);
            CREATE TABLE entries(id INTEGER PRIMARY KEY,kind TEXT,title TEXT,place TEXT,start TEXT,end TEXT,description TEXT,category TEXT,user_id INTEGER,trip_id INTEGER,guide_key TEXT,sort_order INTEGER,attraction_id INTEGER);
            INSERT INTO trips VALUES(1,'Europa','2026-10-27');
            INSERT INTO users VALUES(1,'admin');
            INSERT INTO entries(id,kind,title,trip_id,guide_key) VALUES(10,'tour','Museu do Louvre',1,'paris-louvre');
            INSERT INTO entries(id,kind,title,trip_id,attraction_id) VALUES(11,'diary','Nossa memória',1,10);
            INSERT INTO entries(id,kind,title,start,trip_id) VALUES(12,'logistics','Chegada Paris','2026-11-01T23:00',1);''')
            args=('paris2026.json','europa-paris-champagne-202611-v1','paris')
            apply_file(c,*args)
            self.assertEqual(c.execute('SELECT start FROM entries WHERE id=10').fetchone()[0],'2026-11-02T09:30')
            self.assertEqual(c.execute('SELECT start FROM entries WHERE id=12').fetchone()[0],'2026-11-01T23:00')
            self.assertEqual(c.execute('SELECT attraction_id FROM entries WHERE id=11').fetchone()[0],10)
            self.assertEqual(c.execute("SELECT start FROM entries WHERE guide_key='champagne-reims'").fetchone()[0],'2026-11-05T07:30')
            apply_file(c,*args)
            self.assertEqual(c.execute("SELECT count(*) FROM entries WHERE guide_key='champagne-reims'").fetchone()[0],1)
        finally:c.close()

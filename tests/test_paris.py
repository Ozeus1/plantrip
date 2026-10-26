import json,sqlite3,unittest
from pathlib import Path
from roma2026 import apply_file
ROOT=Path(__file__).resolve().parents[1]

class ParisFiveDays(unittest.TestCase):
    def test_migration_preserves_memories_and_places_louvre_on_open_day(self):
        c=sqlite3.connect(':memory:')
        try:
            c.executescript('''CREATE TABLE migrations(name TEXT PRIMARY KEY);
            CREATE TABLE trips(id INTEGER,name TEXT,start TEXT);
            CREATE TABLE users(id INTEGER,role TEXT);
            CREATE TABLE entries(id INTEGER PRIMARY KEY,kind TEXT,title TEXT,place TEXT,start TEXT,end TEXT,description TEXT,category TEXT,user_id INTEGER,trip_id INTEGER,guide_key TEXT,sort_order INTEGER,attraction_id INTEGER);
            INSERT INTO trips VALUES(1,'Europa','2026-10-27'); INSERT INTO users VALUES(1,'admin');
            INSERT INTO entries(id,kind,title,trip_id,guide_key,start) VALUES(10,'tour','Museu do Louvre',1,'paris-louvre','2026-11-02T09:30');
            INSERT INTO entries(id,kind,title,trip_id,attraction_id) VALUES(11,'diary','Memória antiga',1,10);
            INSERT INTO entries(id,kind,title,start,trip_id) VALUES(12,'logistics','Chegada Paris','2026-11-01T23:00',1);''')
            args=('paris_five_days.json','europa-paris-five-days-202611-v1','paris-five-days')
            apply_file(c,*args)
            rows=c.execute("SELECT guide_key,start FROM entries WHERE kind='tour' AND start<>''").fetchall()
            self.assertEqual(len(rows),26)
            self.assertEqual(c.execute('SELECT attraction_id FROM entries WHERE id=11').fetchone()[0],10)
            self.assertEqual(c.execute('SELECT start FROM entries WHERE id=12').fetchone()[0],'2026-11-01T23:00')
            self.assertEqual(c.execute('SELECT start FROM entries WHERE id=10').fetchone()[0],'2026-11-06T09:00')
            self.assertEqual([sum(r[1].startswith('2026-11-'+d) for r in rows) for d in ['02','03','04','05','06']],[7,9,3,2,5])
            self.assertEqual(c.execute("SELECT start FROM entries WHERE guide_key='paris-garenord'").fetchone()[0],'')
            c.execute("UPDATE entries SET start='2026-11-06T09:30' WHERE id=10")
            apply_file(c,*args)
            self.assertEqual(c.execute('SELECT start FROM entries WHERE id=10').fetchone()[0],'2026-11-06T09:30')
        finally:c.close()

    def test_guides_explain_closures_and_two_champagne_houses(self):
        g=json.loads((ROOT/'guides.json').read_text(encoding='utf-8'))
        active=[v for v in g.values() if v.get('paris_day')]
        self.assertEqual(len(active),26)
        for v in active:
            self.assertEqual(len(v['route_summary']),5)
            self.assertGreaterEqual(len({p['source'] for p in v['photos']}),2)
        self.assertIn('fechado',g['paris-pompidou']['booking'].lower())
        self.assertEqual(g['champagne-reims']['paris_day'],3)
        self.assertEqual(g['champagne-ruinart']['paris_day'],3)
        self.assertIn('cadeira',g['champagne-ruinart']['accessibility'])
        self.assertNotIn('paris_day',g['paris-outlet'])
        self.assertNotIn('paris_day',g['paris-garenord'])

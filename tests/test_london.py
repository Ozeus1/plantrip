import json,sqlite3,unittest
from pathlib import Path
from roma2026 import apply_file
ROOT=Path(__file__).resolve().parents[1]

class LondonItinerary(unittest.TestCase):
    def test_two_days_keep_existing_memories_and_transport(self):
        c=sqlite3.connect(':memory:')
        try:
            c.executescript('''CREATE TABLE migrations(name TEXT PRIMARY KEY);
            CREATE TABLE trips(id INTEGER,name TEXT,start TEXT);
            CREATE TABLE users(id INTEGER,role TEXT);
            CREATE TABLE entries(id INTEGER PRIMARY KEY,kind TEXT,title TEXT,place TEXT,start TEXT,end TEXT,description TEXT,category TEXT,user_id INTEGER,trip_id INTEGER,guide_key TEXT,sort_order INTEGER,attraction_id INTEGER);
            INSERT INTO trips VALUES(1,'Europa','2026-10-27'); INSERT INTO users VALUES(1,'admin');
            INSERT INTO entries(id,kind,title,trip_id,guide_key,start) VALUES(10,'tour','Tower of London e Tower Bridge',1,'londres-tower','2026-11-10T09:30');
            INSERT INTO entries(id,kind,title,trip_id,attraction_id) VALUES(11,'diary','Memória antiga',1,10);
            INSERT INTO entries(id,kind,title,start,trip_id) VALUES(12,'logistics','Saída Londres','2026-11-12T06:00',1);
            INSERT INTO entries(id,kind,title,trip_id,guide_key,start) VALUES(13,'tour','British Museum',1,'londres-british','2026-11-11T10:00');''')
            args=('london_two_days.json','europa-london-two-days-202611-v1','london-two-days')
            apply_file(c,*args)
            tours=c.execute("SELECT start,title FROM entries WHERE kind='tour' AND start<>'' ORDER BY start").fetchall()
            self.assertEqual(len(tours),13)
            self.assertEqual(sum(x[0].startswith('2026-11-09') for x in tours),7)
            self.assertEqual(sum(x[0].startswith('2026-11-10') for x in tours),6)
            self.assertEqual(c.execute('SELECT attraction_id FROM entries WHERE id=11').fetchone()[0],10)
            self.assertEqual(c.execute('SELECT start FROM entries WHERE id=12').fetchone()[0],'2026-11-12T06:00')
            self.assertEqual(c.execute('SELECT start FROM entries WHERE id=13').fetchone()[0],'')
            c.execute("UPDATE entries SET start='2026-11-10T09:15' WHERE id=10")
            apply_file(c,*args)
            self.assertEqual(c.execute('SELECT start FROM entries WHERE id=10').fetchone()[0],'2026-11-10T09:15')
        finally:c.close()

    def test_guides_document_selection_and_access_limitations(self):
        guides=json.loads((ROOT/'guides.json').read_text(encoding='utf-8'))
        london=[g for g in guides.values() if g.get('london_day')]
        self.assertEqual(len(london),12)
        for g in london:
            self.assertGreaterEqual(len({p['source'] for p in g['photos']}),2)
            self.assertEqual(len(g['route_summary']),2)
            self.assertGreaterEqual(len(g['alternatives']),8)
            self.assertTrue(g['accessibility'])
        self.assertIn('15h15',guides['londres-city']['booking'])
        self.assertTrue(any('09' in g['route_summary'][0]['date'] for g in london))
        alternatives=guides['londres-city']['alternatives']
        self.assertTrue(any('Fifteen' in a['name'] and 'fechou' in a['text'] for a in alternatives))
        self.assertFalse(any(any(x in a['name'] for x in ('British Museum','Sherlock','Madame Tussauds')) for a in alternatives))

    def test_no_museums_migration_preserves_entry_and_updates_afternoon(self):
        data=json.loads((ROOT/'london_without_museums.json').read_text(encoding='utf-8'))
        stages={s['key']:s for s in data['stages']}
        self.assertEqual(stages['londres-tate']['start'],'')
        self.assertEqual(stages['londres-british']['start'],'')
        self.assertEqual(stages['londres-city']['start'],'2026-11-10T15:15')
        guides=json.loads((ROOT/'guides.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(guides['londres-tate']['photos']),2)
        self.assertNotIn('london_day',guides['londres-tate'])

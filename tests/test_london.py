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
        self.assertEqual(len(london),24)
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


class MergedItineraries(unittest.TestCase):
    def database(self):
        c=sqlite3.connect(':memory:')
        c.executescript('''CREATE TABLE migrations(name TEXT PRIMARY KEY);
        CREATE TABLE trips(id INTEGER,name TEXT,start TEXT);
        CREATE TABLE users(id INTEGER,role TEXT);
        CREATE TABLE entries(id INTEGER PRIMARY KEY,kind TEXT,title TEXT,place TEXT,start TEXT,end TEXT,description TEXT,category TEXT,user_id INTEGER,trip_id INTEGER,guide_key TEXT,sort_order INTEGER,attraction_id INTEGER);
        INSERT INTO trips VALUES(1,'Europa','2026-10-27'); INSERT INTO users VALUES(1,'admin');
        INSERT INTO entries(id,kind,title,start,end,description,trip_id,guide_key,sort_order) VALUES(10,'tour','Pantheon','2026-10-29T15:30','2026-10-29T16:15','DIA 1 — CENTRO HISTÓRICO | Parada 3: Pantheon. Nota do admin',1,'roma-pantheon',5);
        INSERT INTO entries(id,kind,title,trip_id,attraction_id) VALUES(11,'diary','Memória',1,10);
        INSERT INTO entries(id,kind,title,start,end,description,trip_id,guide_key) VALUES(20,'tour','Abadia de Westminster','2026-11-09T11:45','2026-11-09T13:00','DIA 1 — X | Parada 3: Abadia. Visita turística. 11h45 é proposta, não bilhete comprado.',1,'londres-westminster');''')
        return c
    def test_rome_adds_sant_ignazio_and_keeps_existing_entries(self):
        from roma2026 import apply_merge
        c=self.database()
        try:
            apply_merge(c,'roma_sant_ignazio.json','m1','test')
            row=c.execute("SELECT title,start,end,place,category FROM entries WHERE guide_key='roma-santignazio'").fetchone()
            self.assertEqual(row,('Igreja de Santo Inácio de Loyola (Sant’Ignazio)','2026-10-29T15:25','2026-10-29T15:50','Roma','Passeio'))
            old=c.execute('SELECT start,end,description,sort_order FROM entries WHERE id=10').fetchone()
            self.assertEqual(old[:2],('2026-10-29T16:00','2026-10-29T16:45'))
            self.assertIn('Parada 4: Pantheon',old[2]);self.assertIn('Nota do admin',old[2]);self.assertIsNone(old[3])
            self.assertEqual(c.execute('SELECT attraction_id FROM entries WHERE id=11').fetchone()[0],10)
            count=c.execute('SELECT count(*) FROM entries').fetchone()[0]
            apply_merge(c,'roma_sant_ignazio.json','m1','test')
            self.assertEqual(c.execute('SELECT count(*) FROM entries').fetchone()[0],count)
        finally:c.close()
    def test_london_merge_adds_twelve_stops_and_reorders_days(self):
        from roma2026 import apply_merge
        c=self.database()
        try:
            old=next(r[0] for st in json.loads((ROOT/'london_merged.json').read_text(encoding='utf-8'))['stages'] if st['key']=='londres-westminster' for r in st['replace'])
            c.execute('UPDATE entries SET description=? WHERE id=20',('DIA 1 — X | Parada 3: Abadia.\n\n'+old+'\n\nMobilidade: ...',))
            apply_merge(c,'london_merged.json','m2','test')
            abbey=c.execute('SELECT start,end,description FROM entries WHERE id=20').fetchone()
            self.assertEqual(abbey[:2],('2026-11-09T13:35','2026-11-09T14:50'))
            self.assertIn('Parada 7',abbey[2]);self.assertIn('13h35 é proposta',abbey[2]);self.assertNotIn('11h45',abbey[2])
            added=c.execute("SELECT substr(start,1,10),count(*) FROM entries WHERE kind='tour' AND guide_key LIKE 'londres-%' AND id<>20 GROUP BY 1").fetchall()
            self.assertEqual(added,[('2026-11-09',5),('2026-11-10',7)])
            self.assertEqual(c.execute("SELECT start FROM entries WHERE guide_key='londres-mall'").fetchone()[0],'2026-11-09T11:30')
        finally:c.close()
    def test_guides_stay_consistent_with_stage_files(self):
        guides=json.loads((ROOT/'guides.json').read_text(encoding='utf-8'))
        places=json.loads((ROOT/'places.json').read_text(encoding='utf-8'))['guides']
        for filename in ('roma_sant_ignazio.json','london_merged.json'):
            for stage in json.loads((ROOT/filename).read_text(encoding='utf-8'))['stages']:
                self.assertIn(stage['key'],guides);self.assertIn(stage['key'],places)
        for day in (1,2):
            day_guides=sorted((g for g in guides.values() if g.get('london_day')==day),key=lambda g:g['route_sequence'])
            self.assertEqual([g['route_sequence'] for g in day_guides],list(range(1,13)))
            self.assertEqual([g['title'] for g in day_guides],guides['londres-city']['route_summary'][day-1]['places'])
            for g in day_guides:self.assertTrue(g['kicker'].endswith(f"Parada {g['route_sequence']}"))

import unittest, subprocess, tempfile, os, sys, time, json, urllib.request, urllib.error, http.cookiejar, socket
from pathlib import Path

class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        with socket.socket() as s:
            s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
        cls.url=f'http://127.0.0.1:{port}'
        cls.process=subprocess.Popen([sys.executable,'app.py'],cwd=Path(__file__).resolve().parents[1],env={**os.environ,'PORT':str(port),'DATA_DIR':cls.tmp.name},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        cls.admin=cls.client(); cls.member=cls.client()
        for _ in range(80):
            try:cls.call(cls.admin,'/api/state');break
            except OSError:time.sleep(.1)
        else:raise RuntimeError('Servidor não iniciou')

    @staticmethod
    def client():return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate();cls.process.wait();cls.tmp.cleanup()

    @classmethod
    def call(cls,client,path,data=None,headers=None):
        raw=json.dumps(data).encode() if isinstance(data,dict) else data
        h={'Content-Type':'application/json'} if isinstance(data,dict) else {}
        h.update(headers or {})
        with client.open(urllib.request.Request(cls.url+path,data=raw,headers=h)) as r:
            body=r.read()
            return json.loads(body) if r.headers.get('Content-Type','').startswith('application/json') else body

    def test_complete_trip_and_access(self):
        call=self.call; a=self.admin;m=self.member
        self.assertTrue(call(a,'/api/state')['setup'])
        call(a,'/api/setup',{'name':'Admin','email':'admin@test.com','password':'abcdefgh'})
        self.assertEqual(call(a,'/api/state')['user']['role'],'admin')
        initial=call(a,'/api/state');tid=initial['trip_id']
        self.assertEqual(initial['trips'][0]['name'],'Europa')
        self.assertEqual(initial['trips'][0]['start'],'2026-10-27')
        departure=next(e for e in initial['entries'] if e['title']=='Viagem Roma → Paris')
        self.assertEqual(departure['start'],'2026-11-01T18:00')
        self.assertEqual(departure['end'],'2026-11-01T23:00')
        stages=[e['title'] for e in initial['entries'] if e['kind']=='logistics']
        for title in ['Voo Fortaleza → Madrid','Voo Madrid → Roma','Hotel Roma','Viagem Roma → Paris','Hotel Paris','Viagem Paris → Londres','Hotel Londres','Viagem Londres → Madrid','Hotel Madrid','Viagem Madrid → Fortaleza']:self.assertEqual(stages.count(title),1,title)
        self.assertNotIn('Chegada a Paris',stages)
        self.assertEqual(len([e for e in initial['entries'] if e['kind']=='tour']),31)
        tours=[e for e in initial['entries'] if e['kind']=='tour']
        for tour in tours:
            guide=call(a,f"/api/attractions/{tour['id']}")
            self.assertEqual(guide['guide']['key'],tour['guide_key'])
            self.assertEqual(len(guide['guide']['stops']),3)
            self.assertGreaterEqual(len(guide['guide']['history']),2)
            self.assertIn(b'attractions.js',call(a,f"/attractions/{tour['id']}"))
        with self.assertRaises(urllib.error.HTTPError) as ex:call(self.client(),f"/api/attractions/{tours[0]['id']}")
        self.assertEqual(ex.exception.code,401)
        call(a,'/api/members',{'name':'Viajante','email':'member@test.com','password':'abcdefgh','trip_id':tid})
        call(m,'/api/login',{'email':'member@test.com','password':'abcdefgh'})
        order_ids=[e['id'] for e in initial['entries'] if e['kind']=='logistics']
        reversed_ids=list(reversed(order_ids))
        order_payload={'trip_id':tid,'kind':'logistics','entry_ids':reversed_ids}
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,'/api/entries/reorder',order_payload)
        self.assertEqual(ex.exception.code,403)
        call(a,'/api/entries/reorder',order_payload)
        for client in (a,m):
            ordered=call(client,'/api/state')['entries']
            self.assertEqual([e['id'] for e in ordered if e['kind']=='logistics'],reversed_ids)
            self.assertEqual([e['id'] for e in ordered if e['kind']=='tour'],[e['id'] for e in tours])
        import sqlite3
        persisted=sqlite3.connect(Path(self.tmp.name)/'plantrip.db')
        try:
            self.assertEqual([r[0] for r in persisted.execute("SELECT id FROM entries WHERE trip_id=? AND kind='logistics' ORDER BY sort_order",(tid,))],reversed_ids)
        finally:persisted.close()
        for invalid,status in [(reversed_ids[:-1],409),(reversed_ids+[reversed_ids[0]],400),(reversed_ids+[tours[0]['id']],409),(['wrong'],400)]:
            with self.assertRaises(urllib.error.HTTPError) as ex:call(a,'/api/entries/reorder',{**order_payload,'entry_ids':invalid})
            self.assertEqual(ex.exception.code,status)
        tail=call(a,'/api/entries',{'kind':'logistics','title':'Etapa adicionada depois da ordenação','trip_id':tid})['id']
        self.assertEqual([e['id'] for e in call(a,'/api/state')['entries'] if e['kind']=='logistics'],reversed_ids+[tail])
        call(a,'/api/delete',{'entry_id':tail})
        call(a,'/api/entries/reorder',{'trip_id':tid,'kind':'logistics','reset':True})
        restored=[e for e in call(a,'/api/state')['entries'] if e['kind']=='logistics']
        self.assertEqual([e['id'] for e in restored],order_ids)
        original_dates={e['id']:(e['start'],e['end']) for e in initial['entries']}
        self.assertTrue(all((e['start'],e['end'])==original_dates[e['id']] for e in restored))
        tour_ids=[e['id'] for e in tours]
        call(a,'/api/entries/reorder',{'trip_id':tid,'kind':'tour','entry_ids':list(reversed(tour_ids))})
        self.assertEqual([e['id'] for e in call(m,'/api/state')['entries'] if e['kind']=='tour'],list(reversed(tour_ids)))
        call(a,'/api/entries/reorder',{'trip_id':tid,'kind':'tour','reset':True})
        self.assertEqual(call(m,f"/api/attractions/{tours[0]['id']}")['entry']['id'],tours[0]['id'])
        renamed={**tours[0],'title':'Passeio com nome personalizado'}
        call(a,'/api/entries',renamed)
        self.assertEqual(call(a,f"/api/attractions/{tours[0]['id']}")['guide']['key'],tours[0]['guide_key'])
        p={'kind':'logistics','title':'Voo a Paris','start':'2026-11-01T12:00','end':'2026-11-01T15:00','place':'Paris','category':'Voo','trip_id':tid}
        eid=call(a,'/api/entries',p)['id']
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,'/api/entries',p)
        self.assertEqual(ex.exception.code,403)
        call(a,'/api/entries',{**p,'id':eid,'title':'Voo corrigido'})
        hotel=next(e for e in initial['entries'] if e['title']=='Hotel Paris')['id']
        call(a,'/api/upload',b'%PDF-1.4 voucher',{'X-Entry-Id':str(hotel),'X-File-Name':'voucher%20paris.pdf'})
        call(a,'/api/upload',b'PNG-data',{'X-Entry-Id':str(hotel),'X-File-Name':'reserva.png'})
        docs=next(e for e in call(m,'/api/state')['entries'] if e['id']==hotel)['files']
        self.assertEqual([f['name'] for f in docs],['voucher paris.pdf','reserva.png'])
        self.assertTrue(call(m,f'/media/{docs[0]["id"]}').startswith(b'%PDF'))
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,'/api/upload',b'%PDF-x',{'X-Entry-Id':str(hotel),'X-File-Name':'x.pdf'})
        self.assertEqual(ex.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,'/api/delete-file',{'entry_id':hotel,'file_id':docs[0]['id']})
        self.assertEqual(ex.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as ex:call(a,'/api/delete-file',{'entry_id':eid,'file_id':docs[0]['id']})
        self.assertEqual(ex.exception.code,400)
        call(a,'/api/delete-file',{'entry_id':hotel,'file_id':docs[0]['id']})
        left=next(e for e in call(a,'/api/state')['entries'] if e['id']==hotel)['files']
        self.assertEqual([f['name'] for f in left],['reserva.png'])
        self.assertEqual(len(list((Path(self.tmp.name)/'uploads').iterdir())),1)
        call(a,'/api/delete-file',{'entry_id':hotel,'file_id':left[0]['id']})
        call(m,'/api/comments',{'entry_id':eid,'body':'Vamos juntos!'})
        diary=call(m,'/api/entries',{'kind':'diary','title':'Nossa chegada','place':'Paris','trip_id':tid,'attraction_id':tours[0]['id']})['id']
        call(m,'/api/upload',b'%PDF-1.4\n%%EOF',{'X-Entry-Id':str(diary),'X-File-Name':'reserva.pdf'})
        state=call(a,'/api/state'); entry=next(e for e in state['entries'] if e['id']==diary)
        self.assertEqual(entry['attraction_id'],tours[0]['id'])
        fid=entry['files'][0]['id']
        self.assertTrue(call(a,f'/media/{fid}').startswith(b'%PDF'))
        with self.assertRaises(urllib.error.HTTPError) as ex:call(self.client(),f'/media/{fid}')
        self.assertEqual(ex.exception.code,401)
        flight=next(e for e in state['entries'] if e['id']==eid)
        self.assertEqual(flight['title'],'Voo corrigido')
        self.assertEqual(len(flight['comments']),1)
        with self.assertRaises(urllib.error.HTTPError):call(m,'/api/delete',{'entry_id':eid})
        with self.assertRaises(urllib.error.HTTPError):call(m,'/api/upload',b'<script>',{'X-Entry-Id':str(diary),'X-File-Name':'bad.html'})
        other=call(a,'/api/trips',{'name':'Outro grupo','start':'2027-01-01','end':'2027-01-10','places':'Brasil','member_ids':[]})['id']
        private_tour=call(a,'/api/entries',{'kind':'tour','title':'Passeio privado','trip_id':other})['id']
        with self.assertRaises(urllib.error.HTTPError) as ex:call(a,'/api/entries/reorder',{'trip_id':tid,'kind':'tour','entry_ids':tour_ids+[private_tour]})
        self.assertEqual(ex.exception.code,409)
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,f'/api/attractions/{private_tour}')
        self.assertEqual(ex.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,'/api/entries',{'kind':'diary','title':'Vínculo incorreto','trip_id':tid,'attraction_id':private_tour})
        self.assertEqual(ex.exception.code,400)
        secret=call(a,'/api/entries',{'kind':'diary','title':'Privado','trip_id':other})['id']
        call(a,'/api/upload',b'%PDF-secret',{'X-Entry-Id':str(secret),'X-File-Name':'private.pdf'})
        private_state=call(a,f'/api/state?trip_id={other}')
        private_file=next(e for e in private_state['entries'] if e['id']==secret)['files'][0]['id']
        for path,data in [(f'/api/state?trip_id={other}',None),(f'/media/{private_file}',None),('/api/comments',{'entry_id':secret,'body':'Invasão'}),('/api/entries',{'trip_id':other,'kind':'diary','title':'Invasão'}),('/api/users',{'name':'X','email':'x@x.com','password':'abcdefgh'}),('/api/trips',{'name':'Proibido'})]:
            with self.assertRaises(urllib.error.HTTPError) as ex:call(m,path,data)
            self.assertEqual(ex.exception.code,403)
        self.assertEqual(len(call(m,'/api/state')['trips']),1)
        member_id=call(m,'/api/state')['user']['id']
        call(a,'/api/users',{'id':member_id,'name':'Nome atualizado','email':'member@test.com'})
        call(a,'/api/trips',{'id':other,'name':'Outro grupo','start':'2027-01-01','end':'2027-01-10','places':'Brasil','member_ids':[member_id]})
        self.assertEqual(len(call(m,'/api/state')['trips']),2)
        self.assertEqual(call(m,f'/media/{private_file}'),b'%PDF-secret')
        call(a,'/api/trips',{'id':other,'name':'Outro grupo','start':'2027-01-01','end':'2027-01-10','places':'Brasil','member_ids':[]})
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,f'/media/{private_file}')
        self.assertEqual(ex.exception.code,403)
        call(a,'/api/delete',{'entry_id':secret})
        call(m,'/api/delete',{'entry_id':diary})
        self.assertFalse(list((Path(self.tmp.name)/'uploads').iterdir()))
        call(m,'/api/logout',{})
        self.assertIsNone(call(m,'/api/state')['user'])
        self.assertIn(b'plantrip',call(a,'/'))

class Migration(unittest.TestCase):
    def test_preserve_old_content_and_seed_once(self):
        import app,sqlite3
        original=app.DATA
        with tempfile.TemporaryDirectory() as tmp:
            try:
                app.DATA=Path(tmp)
                with sqlite3.connect(Path(tmp)/'plantrip.db') as c:
                    c.executescript("CREATE TABLE users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT,salt TEXT,role TEXT); CREATE TABLE entries(id INTEGER PRIMARY KEY,kind TEXT,title TEXT,place TEXT,start TEXT,end TEXT,description TEXT,category TEXT,user_id INTEGER REFERENCES users(id)); INSERT INTO users VALUES(1,'Admin','a@b.c','x','x','admin'); INSERT INTO entries VALUES(1,'diary','Memória antiga','Roma','','','','Memória',1);")
                c.close()
                app.init();app.init()
                with app.db() as c:
                    self.assertEqual(c.execute('SELECT count(*) FROM trips').fetchone()[0],2)
                    self.assertEqual(c.execute("SELECT count(*) FROM entries WHERE kind='tour'").fetchone()[0],31)
                    row=c.execute('SELECT t.name FROM entries e JOIN trips t ON t.id=e.trip_id WHERE e.id=1').fetchone()
                    self.assertEqual(row[0],'Minha viagem anterior')
                    self.assertEqual(c.execute("SELECT count(*) FROM entries WHERE kind='logistics' AND title LIKE 'Hotel %'").fetchone()[0],4)
                    self.assertEqual(c.execute("SELECT count(*) FROM entries WHERE kind='logistics' AND title='Chegada a Paris'").fetchone()[0],0)
            finally:app.DATA=original

if __name__=='__main__':unittest.main()

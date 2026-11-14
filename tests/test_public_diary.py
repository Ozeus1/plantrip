import unittest
import test_app

class PublicDiary(test_app.Integration):
    def test_complete_trip_and_access(self):
        call=self.call;a=self.admin;guest=self.client()
        call(a,'/api/setup',{'name':'Admin','email':'admin@public.test','password':'abcdefgh'})
        state=call(a,'/api/state');trip=state['trips'][0];tid=trip['id']
        self.assertEqual(call(guest,'/api/public/diary')['entries'],[])
        call(a,'/api/members',{'name':'Companheiro','email':'member@public.test','password':'abc12','trip_id':tid})
        m=self.member;call(m,'/api/login',{'email':'member@public.test','password':'abc12'})
        diary=call(m,'/api/entries',{'kind':'diary','title':'Memória pública','description':'Nosso passeio','place':'Roma','trip_id':tid})['id']
        call(m,'/api/upload',b'image-data',{'X-Entry-Id':str(diary),'X-File-Name':'memory.jpg'})
        call(m,'/api/upload',b'%PDF-private',{'X-Entry-Id':str(diary),'X-File-Name':'document.pdf'})
        call(m,'/api/comments',{'entry_id':diary,'body':'Boa viagem!'})
        logistics=next(e['id'] for e in state['entries'] if e['kind']=='logistics')
        call(a,'/api/upload',b'private-reservation',{'X-Entry-Id':str(logistics),'X-File-Name':'reservation.jpg'})
        reservation=next(e for e in call(a,'/api/state')['entries'] if e['id']==logistics)['files'][0]['id']
        files=next(e for e in call(a,'/api/state')['entries'] if e['id']==diary)['files']
        photo=next(f['id'] for f in files if f['mime']=='image/jpeg');pdf=next(f['id'] for f in files if f['mime']=='application/pdf')
        call(a,'/api/trips',{**trip,'public_diary':True})
        public=call(guest,'/api/public/diary')
        self.assertEqual(len(public['entries']),1)
        post=public['entries'][0]
        self.assertEqual(post['title'],'Memória pública')
        self.assertEqual([f['id'] for f in post['files']],[photo])
        self.assertEqual(post['comments'][0]['body'],'Boa viagem!')
        self.assertNotIn('email',str(public));self.assertNotIn('password',str(public));self.assertNotIn('notes',str(public));self.assertNotIn('member_ids',str(public))
        self.assertEqual(call(guest,f'/media/{photo}'),b'image-data')
        import urllib.error
        for path,data in [(f'/media/{pdf}',None),(f'/media/{reservation}',None),('/api/comments',{'entry_id':diary,'body':'Anônimo'}),('/api/entries',{'kind':'diary','trip_id':tid,'title':'Anônimo'}),('/api/upload',b'file')]:
            with self.assertRaises(urllib.error.HTTPError) as ex:call(guest,path,data)
            self.assertEqual(ex.exception.code,401)
        self.assertIsNone(call(guest,'/api/state')['user'])
        self.assertIn(b'public-diary.js',call(guest,'/diary'))
        call(a,'/api/trips',{**trip,'public_diary':False})
        self.assertEqual(call(guest,'/api/public/diary')['entries'],[])
        with self.assertRaises(urllib.error.HTTPError) as ex:call(guest,f'/media/{photo}')
        self.assertEqual(ex.exception.code,401)


class PublicMap(test_app.Integration):
    def test_complete_trip_and_access(self):
        call=self.call;a=self.admin;guest=self.client()
        call(a,'/api/setup',{'name':'Admin','email':'admin@map.test','password':'abcdefgh'})
        state=call(a,'/api/state');trip=state['trips'][0];tid=trip['id']
        tour=next(e for e in state['entries'] if e['kind']=='tour' and e['guide_key']=='roma-coliseu')
        def memory(title,place,**extra):
            eid=call(a,'/api/entries',{'kind':'diary','title':title,'place':place,'trip_id':tid,'start':'2026-10-30T10:00',**extra})['id']
            call(a,'/api/upload',b'image-data',{'X-Entry-Id':str(eid),'X-File-Name':'photo.jpg'})
            return eid
        linked=memory('Tarde antiga','texto livre',attraction_id=tour['id'])
        by_text=memory('Coliseu de manhã','coliseu')
        city=memory('Jantar','Londres')
        nowhere=memory('Sem pista','Marte')
        no_photo=call(a,'/api/entries',{'kind':'diary','title':'Sem foto','place':'Paris','trip_id':tid})['id']
        self.assertEqual(call(guest,'/api/public/diary')['map']['points'],[])
        call(a,'/api/trips',{**trip,'public_diary':True})
        data=call(guest,'/api/public/diary')['map']
        points={p['id']:p for p in data['points']}
        coliseu=next(p for p in data['points'] if p['level']=='attraction' and p['name']=='Coliseu')
        self.assertEqual(sorted(coliseu['entry_ids']),sorted([linked,by_text]))
        self.assertAlmostEqual(coliseu['lat'],41.8902,3)
        roma=next(p for p in data['points'] if p['level']=='city' and p['name']=='Roma')
        self.assertEqual(sorted(roma['entry_ids']),sorted([linked,by_text]))
        london=next(p for p in data['points'] if p['level']=='attraction' and p['name'].startswith('Londres'))
        self.assertEqual(london['entry_ids'],[city])
        europe=next(p for p in data['points'] if p['level']=='trip')
        self.assertEqual(sorted(europe['entry_ids']),sorted([linked,by_text,city]))
        self.assertEqual(data['unlocated'],[nowhere])
        self.assertNotIn(no_photo,[i for p in data['points'] for i in p['entry_ids']])
        self.assertNotIn('password',str(data))
        poi=next(p for p in data['points'] if p.get('kind')=='poi')
        self.assertEqual((poi['name'],poi['city']),('Saint-Denis','Paris'));self.assertEqual(poi['entry_ids'],[])
        origin=next(p for p in data['points'] if p['level']=='origin')
        self.assertEqual(origin['name'],'Fortaleza')
        meta=data['trips'][0]
        self.assertEqual((meta['start'],meta['end']),(trip['start'],trip['end']))
        self.assertEqual(meta['countries'],['Itália','Reino Unido','França']);self.assertEqual(meta['origin']['country'],'Brasil');self.assertEqual(meta['route'],[])
        self.assertNotIn('Brasil',meta['countries'])
        private=call(a,'/api/state')['map']
        self.assertGreater(len([p for p in private['points'] if p['level']=='attraction' and not p['entry_ids']]),20)
        self.assertEqual(private['trips'][0]['route'],['Roma','Paris','Londres','Madrid'])
        self.assertIn('Espanha',private['trips'][0]['countries'])
        photo=memory('Basílica','Saint-Denis')
        again=call(a,'/api/state')['map']
        self.assertEqual(next(p for p in again['points'] if p.get('kind')=='poi')['entry_ids'],[photo])


if __name__=='__main__':unittest.main()

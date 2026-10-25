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

if __name__=='__main__':unittest.main()

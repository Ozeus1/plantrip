import base64
import urllib.error
import test_app


class AccountsAndDocuments(test_app.Integration):
    def test_complete_trip_and_access(self):
        call=self.call;a=self.admin;m=self.member
        call(a,'/api/setup',{'name':'Admin','email':'admin@test.com','password':'abcdefgh'})
        initial=call(a,'/api/state');tid=initial['trip_id']
        photo='data:image/png;base64,'+base64.b64encode(bytes.fromhex('89504e470d0a1a0a')+b'test-image').decode()
        uid=call(a,'/api/users',{'name':'Ana','email':'ana@test.com','login':'Ana.Rosa','photo':photo,'password':'initial123'})['id']
        member=next(u for u in call(a,'/api/state')['users'] if u['id']==uid)
        self.assertEqual(member['login'],'ana.rosa');self.assertEqual(member['photo'],photo)
        trip=initial['trips'][0]
        call(a,'/api/trips',{**trip,'public_diary':False,'member_ids':[uid]})
        call(m,'/api/login',{'email':'ANA.ROSA','password':'initial123'})
        self.assertEqual(call(m,'/api/state')['user']['id'],uid)
        call(self.client(),'/api/login',{'email':'ana@test.com','password':'initial123'})
        for payload in [
            {'name':'Outro','email':'other@test.com','login':'ANA.ROSA','password':'initial123'},
            {'name':'Outro','email':'other@test.com','login':'bad login','password':'initial123'},
            {'name':'Outro','email':'other@test.com','login':'valid','photo':'data:image/svg+xml;base64,abcd','password':'initial123'},
        ]:
            with self.assertRaises(urllib.error.HTTPError) as ex:call(a,'/api/users',payload)
            self.assertEqual(ex.exception.code,400)
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,'/api/users',{'id':uid,'name':'Ana','email':'ana@test.com','login':'changed'})
        self.assertEqual(ex.exception.code,403)
        call(a,'/api/users',{'id':uid,'name':'Ana Rosa','email':'ana@test.com'})
        member=next(u for u in call(a,'/api/state')['users'] if u['id']==uid)
        self.assertEqual(member['login'],'ana.rosa');self.assertEqual(member['photo'],photo)
        payload={'trip_id':tid,'kind':'documents','title':'Passaportes','start':'2026-10-27','end':'2026-10-29'}
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,'/api/entries',payload)
        self.assertEqual(ex.exception.code,403)
        eid=call(a,'/api/entries',payload)['id']
        call(a,'/api/upload',b'%PDF-test',{'X-Entry-Id':str(eid),'X-File-Name':'passaporte.pdf'})
        document=next(e for e in call(m,'/api/state')['entries'] if e['id']==eid)
        self.assertEqual((document['start'],document['end']),('',''))
        fid=document['files'][0]['id']
        self.assertEqual(call(m,f'/media/{fid}'),b'%PDF-test')
        with self.assertRaises(urllib.error.HTTPError) as ex:call(self.client(),f'/media/{fid}')
        self.assertEqual(ex.exception.code,401)
        with self.assertRaises(urllib.error.HTTPError) as ex:call(a,'/api/upload',b'video',{'X-Entry-Id':str(eid),'X-File-Name':'movie.mp4'})
        self.assertEqual(ex.exception.code,400)
        diary=call(m,'/api/entries',{'kind':'diary','title':'Memória','trip_id':tid})['id']
        entry=next(e for e in call(a,'/api/state')['entries'] if e['id']==diary)
        self.assertEqual(entry['author_photo'],photo)
        call(a,'/api/users',{'id':uid,'name':'Ana Rosa','email':'ana@test.com','photo':''})
        self.assertEqual(next(u for u in call(a,'/api/state')['users'] if u['id']==uid)['photo'],'')

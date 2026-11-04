import unittest, urllib.error
import test_app

class UploadLinks(test_app.Integration):
    test_complete_trip_and_access=None  # não repete o teste herdado; este servidor começa sem administrador

    def test_qr_link_publishes_photos(self):
        call=self.call;a=self.admin;guest=self.client()
        call(a,'/api/setup',{'name':'Admin','email':'admin@qr.test','password':'abcdefgh'})
        state=call(a,'/api/state');tid=state['trip_id']
        call(a,'/api/members',{'name':'Fernanda','email':'fe@qr.test','password':'abc12','trip_id':tid})
        call(a,'/api/members',{'name':'Outro','email':'outro@qr.test','password':'abc12','trip_id':tid})
        users={u['email']:u['id'] for u in call(a,'/api/state')['users']}
        fe=users['fe@qr.test']
        link=call(a,'/api/upload-links',{'trip_id':tid,'user_id':fe})
        self.assertEqual(call(a,'/api/upload-links',{'trip_id':tid,'user_id':fe})['token'],link['token'])
        # Página pública responde sem login
        self.assertIn(b'upload.js',call(guest,link['path']))
        info=call(guest,'/api/u/'+link['token'])
        self.assertEqual(info['participant']['name'],'Fernanda')
        self.assertNotIn('email',str(info))
        tour=info['places'][0]['id']
        memory=call(guest,f"/api/u/{link['token']}/memory",{'attraction_id':tour})
        call(guest,f"/api/u/{link['token']}/upload",b'jpeg-bytes',{'X-Entry-Id':str(memory['id']),'X-File-Name':'IMG_1.jpg'})
        with self.assertRaises(urllib.error.HTTPError):
            call(guest,f"/api/u/{link['token']}/upload",b'%PDF',{'X-Entry-Id':str(memory['id']),'X-File-Name':'doc.pdf'})
        created=call(guest,f"/api/u/{link['token']}/memory",{'new_place':'Trattoria do bairro','title':'Jantar','description':'Massa'})
        self.assertNotEqual(created['attraction_id'],tour)
        self.assertEqual(call(guest,f"/api/u/{link['token']}/memory",{'new_place':'trattoria do bairro'})['attraction_id'],created['attraction_id'])
        entries={e['id']:e for e in call(a,'/api/state')['entries']}
        diary=entries[memory['id']]
        self.assertEqual((diary['kind'],diary['user_id'],diary['attraction_id']),('diary',fe,tour))
        self.assertEqual([f['name'] for f in diary['files']],['IMG_1.jpg'])
        self.assertEqual(entries[created['attraction_id']]['kind'],'tour')
        self.assertEqual(entries[created['id']]['title'],'Jantar')
        # Membro comum só vê o próprio link e não pode regenerar
        m=self.member;call(m,'/api/login',{'email':'outro@qr.test','password':'abc12'})
        for body in ({'trip_id':tid,'user_id':fe},{'trip_id':tid,'user_id':users['outro@qr.test'],'regenerate':True}):
            with self.assertRaises(urllib.error.HTTPError) as err:call(m,'/api/upload-links',body)
            self.assertEqual(err.exception.code,403)
        self.assertTrue(call(m,'/api/upload-links',{'trip_id':tid,'user_id':users['outro@qr.test']})['token'])
        # Regenerar invalida o código antigo
        new=call(a,'/api/upload-links',{'trip_id':tid,'user_id':fe,'regenerate':True})
        self.assertNotEqual(new['token'],link['token'])
        with self.assertRaises(urllib.error.HTTPError) as err:call(guest,'/api/u/'+link['token'])
        self.assertEqual(err.exception.code,404)
        # Saindo da viagem, o link deixa de valer
        trip=next(t for t in call(a,'/api/state')['trips'] if t['id']==tid)
        call(a,'/api/trips',{**trip,'public_diary':bool(trip['public_diary']),'member_ids':[i for i in trip['member_ids'] if i!=fe]})
        with self.assertRaises(urllib.error.HTTPError):call(guest,'/api/u/'+new['token'])

if __name__=='__main__':unittest.main()

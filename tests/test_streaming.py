import unittest,urllib.request,urllib.error
import test_app

class MediaStreaming(test_app.Integration):
    def test_complete_trip_and_access(self):
        call=self.call;a=self.admin;guest=self.client()
        call(a,'/api/setup',{'name':'Admin','email':'stream@test.example','password':'initial123'})
        trip=call(a,'/api/state')['trips'][0]
        eid=call(a,'/api/entries',{'kind':'diary','title':'Video','trip_id':trip['id']})['id']
        content=bytes(range(256))*32
        call(a,'/api/upload',content,{'X-Entry-Id':str(eid),'X-File-Name':'sample.mp4'})
        fid=next(e for e in call(a,'/api/state')['entries'] if e['id']==eid)['files'][0]['id']
        path=f'/media/{fid}'
        with self.assertRaises(urllib.error.HTTPError) as ex:call(guest,path,headers={'Range':'bytes=0-3'})
        self.assertEqual(ex.exception.code,401)
        call(a,'/api/trips',{**trip,'public_diary':True})
        for header,start,end in [('bytes=0-31',0,31),('bytes=256-',256,len(content)-1),('bytes=-20',len(content)-20,len(content)-1),('bytes=8100-99999',8100,len(content)-1)]:
            with guest.open(urllib.request.Request(self.url+path,headers={'Range':header})) as r:
                self.assertEqual(r.status,206);self.assertEqual(r.read(),content[start:end+1])
                self.assertEqual(r.headers['Content-Range'],f'bytes {start}-{end}/{len(content)}')
                self.assertEqual(r.headers['Accept-Ranges'],'bytes')
        with guest.open(urllib.request.Request(self.url+path,method='HEAD')) as r:
            self.assertEqual(r.status,200);self.assertEqual(r.read(),b'');self.assertEqual(int(r.headers['Content-Length']),len(content))
        with self.assertRaises(urllib.error.HTTPError) as ex:call(guest,path,headers={'Range':'bytes=99999-'})
        self.assertEqual(ex.exception.code,416);self.assertEqual(ex.exception.headers['Content-Range'],f'bytes */{len(content)}')
        self.assertEqual(call(guest,path,headers={'Range':'bytes=0-3,9-12'}),content)
        with guest.open(urllib.request.Request(self.url+'/api/state',method='HEAD')) as r:self.assertEqual(r.read(),b'')
        call(a,'/api/trips',{**trip,'public_diary':False})
        with self.assertRaises(urllib.error.HTTPError) as ex:call(guest,path,headers={'Range':'bytes=-10'})
        self.assertEqual(ex.exception.code,401)

if __name__=='__main__':unittest.main()

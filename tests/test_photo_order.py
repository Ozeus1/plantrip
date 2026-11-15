import unittest,urllib.error
import test_app

class PhotoOrder(test_app.Integration):
    def test_complete_trip_and_access(self):
        call=self.call;a=self.admin;m=self.member
        call(a,'/api/setup',{'name':'Admin','email':'admin@order.test','password':'initial123'})
        tid=call(a,'/api/state')['trip_id']
        call(a,'/api/members',{'name':'Viajante','email':'member@order.test','password':'member123','trip_id':tid})
        call(m,'/api/login',{'email':'member@order.test','password':'member123'})
        mine=call(m,'/api/entries',{'kind':'diary','trip_id':tid,'title':'Coliseu','place':'Coliseu','start':'2026-10-31'})['id']
        other=call(a,'/api/entries',{'kind':'diary','trip_id':tid,'title':'Outra','place':'Roma','start':'2026-10-31'})['id']
        for name in ('a.jpg','b.jpg','c.jpg'):call(m,'/api/upload',b'img',{'X-Entry-Id':str(mine),'X-File-Name':name})
        call(m,'/api/upload',b'%PDF-1.4',{'X-Entry-Id':str(mine),'X-File-Name':'doc.pdf'})
        call(a,'/api/upload',b'img',{'X-Entry-Id':str(other),'X-File-Name':'z.jpg'})
        def entry(eid):return next(e for e in call(m,'/api/state')['entries'] if e['id']==eid)
        files=entry(mine)['files'];ids=[f['id'] for f in files]
        self.assertEqual([f['name'] for f in files],['a.jpg','b.jpg','c.jpg','doc.pdf'])
        self.assertIsNone(entry(mine)['cover_file_id'])
        foreign=entry(other)['files'][0]['id']

        # Nova ordem: persiste e vale para todos os leitores, também na API pública.
        order=[ids[2],ids[0],ids[3],ids[1]]
        call(m,'/api/files/arrange',{'entry_id':mine,'file_ids':order})
        self.assertEqual([f['id'] for f in entry(mine)['files']],order)
        self.assertEqual([f['id'] for f in next(e for e in call(a,'/api/state')['entries'] if e['id']==mine)['files']],order)

        # Capa: apenas foto desta memória.
        call(m,'/api/files/arrange',{'entry_id':mine,'cover_file_id':ids[1]})
        self.assertEqual(entry(mine)['cover_file_id'],ids[1])
        self.assertEqual([f['id'] for f in entry(mine)['files']],order,'definir a capa não altera a ordem')
        for bad in (ids[3],foreign,999999,True,'x'):
            with self.assertRaises(urllib.error.HTTPError,msg=repr(bad)) as ex:call(m,'/api/files/arrange',{'entry_id':mine,'cover_file_id':bad})
            self.assertEqual(ex.exception.code,400)
        self.assertEqual(entry(mine)['cover_file_id'],ids[1])

        # Ordem inválida: faltando, repetido, de outra memória ou tipo errado.
        for bad in (order[:-1],order+[foreign],[order[0]]*4,'abc',[str(i) for i in order],[True]+order[1:]):
            with self.assertRaises(urllib.error.HTTPError,msg=repr(bad)) as ex:call(m,'/api/files/arrange',{'entry_id':mine,'file_ids':bad})
            self.assertEqual(ex.exception.code,400)
        self.assertEqual([f['id'] for f in entry(mine)['files']],order)

        # Permissão: o autor da memória e o admin; outro membro ou memória alheia, não.
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,'/api/files/arrange',{'entry_id':other,'cover_file_id':foreign})
        self.assertEqual(ex.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as ex:call(self.client(),'/api/files/arrange',{'entry_id':mine,'file_ids':order})
        self.assertIn(ex.exception.code,(401,403))
        call(a,'/api/files/arrange',{'entry_id':mine,'cover_file_id':None})
        self.assertIsNone(entry(mine)['cover_file_id'])

        # Novos arquivos entram no fim; remover a capa limpa a escolha.
        call(m,'/api/files/arrange',{'entry_id':mine,'cover_file_id':ids[1]})
        call(m,'/api/upload',b'img',{'X-Entry-Id':str(mine),'X-File-Name':'d.jpg'})
        self.assertEqual([f['name'] for f in entry(mine)['files']][-1],'d.jpg')
        call(m,'/api/delete-file',{'entry_id':mine,'file_id':ids[1]})
        self.assertIsNone(entry(mine)['cover_file_id'])

    def test_light_versions(self):
        import io,time
        from PIL import Image
        call=self.call;a=self.admin
        tid=call(a,'/api/state')['trip_id']
        eid=call(a,'/api/entries',{'kind':'diary','trip_id':tid,'title':'Grande','place':'Roma','start':'2026-10-31'})['id']
        buf=io.BytesIO();Image.effect_noise((3000,2000),80).convert('RGB').save(buf,'JPEG',quality=95)
        call(a,'/api/upload',buf.getvalue(),{'X-Entry-Id':str(eid),'X-File-Name':'grande.jpg'})
        f=next(e for e in call(a,'/api/state')['entries'] if e['id']==eid)['files'][0]
        self.assertEqual(len(f['v']),8)
        with a.open(self.url+f"/media/{f['id']}?w=480&v={f['v']}") as r:
            self.assertEqual(r.headers['Content-Type'],'image/webp');self.assertIn('max-age',r.headers['Cache-Control']);small=r.read()
        with a.open(self.url+f"/media/{f['id']}") as r:
            self.assertEqual(r.headers['Content-Type'],'image/jpeg');original=r.read()
        self.assertEqual(original,buf.getvalue())
        self.assertLess(len(small)*5,len(original))
        self.assertEqual(Image.open(io.BytesIO(small)).size,(480,320))

if __name__=='__main__':unittest.main()

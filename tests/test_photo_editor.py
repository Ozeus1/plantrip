import io,unittest,urllib.error
import test_app
from PIL import Image

class PhotoEditor(test_app.Integration):
    def test_complete_trip_and_access(self):
        call=self.call;a=self.admin;m=self.member
        call(a,'/api/setup',{'name':'Admin','email':'admin@edit.test','password':'initial123'})
        tid=call(a,'/api/state')['trip_id']
        call(a,'/api/members',{'name':'Viajante','email':'member@edit.test','password':'member123','trip_id':tid})
        call(m,'/api/login',{'email':'member@edit.test','password':'member123'})
        eid=call(m,'/api/entries',{'kind':'diary','trip_id':tid,'title':'Palácio','place':'Madrid','start':'2026-11-12'})['id']
        # 400x200: metade esquerda vermelha, metade direita azul.
        src=Image.new('RGB',(400,200),(200,30,30));src.paste((30,30,200),(200,0,400,200))
        buf=io.BytesIO();src.save(buf,'JPEG',quality=95);sent=buf.getvalue()
        call(m,'/api/upload',sent,{'X-Entry-Id':str(eid),'X-File-Name':'foto.jpg'})
        call(m,'/api/upload',b'%PDF-1.4',{'X-Entry-Id':str(eid),'X-File-Name':'doc.pdf'})
        def files():return next(e for e in call(a,'/api/state')['entries'] if e['id']==eid)['files']
        def pixels(f):
            with a.open(self.url+f"/media/{f['id']}?v={f['v']}") as r:data=r.read()
            return Image.open(io.BytesIO(data)).convert('RGB'),data
        photo,pdf=files();fid=photo['id']
        self.assertFalse(photo['edited'])
        edit=lambda client=a,**ops:call(client,'/api/files/edit',{'entry_id':eid,'file_id':fid,**ops})

        # Só o administrador edita (nem o autor da memória, nem visitante).
        for client in (m,self.client()):
            with self.assertRaises(urllib.error.HTTPError) as ex:edit(client,rotate=90)
            self.assertIn(ex.exception.code,(401,403))
        # Operações inválidas não alteram nada.
        for bad in ({'rotate':45},{'rotate':'90'},{'brightness':3},{'contrast':'1'},{'saturation':0.1},{'crop':{'x':0.5,'y':0,'w':0.7,'h':1}},{'crop':{'x':0,'y':0,'w':0,'h':1}},{'crop':[0,0,1,1]},{'crop':{'x':0,'y':0,'w':0.01,'h':0.01}},{'restore':True}):
            with self.assertRaises(urllib.error.HTTPError,msg=repr(bad)) as ex:edit(**bad)
            self.assertEqual(ex.exception.code,400)
        with self.assertRaises(urllib.error.HTTPError) as ex:call(a,'/api/files/edit',{'entry_id':eid,'file_id':pdf['id'],'rotate':90})
        self.assertEqual(ex.exception.code,400)
        self.assertEqual(pixels(files()[0])[1],sent)

        # Corte: fica só a metade azul; o endereço muda (cache) e a foto passa a constar como editada.
        edit(crop={'x':0.5,'y':0,'w':0.5,'h':1})
        cut=files()[0];img,_=pixels(cut)
        self.assertTrue(cut['edited']);self.assertNotEqual(cut['v'],photo['v']);self.assertEqual(img.size,(200,200))
        r,g,b=img.getpixel((100,100));self.assertGreater(b,150);self.assertLess(r,80)
        with a.open(self.url+f"/media/{fid}?w=480&v={cut['v']}") as r:self.assertEqual(Image.open(io.BytesIO(r.read())).size,(200,200))

        # Nova edição parte da versão atual: girar 90° à direita e clarear.
        edit(crop={'x':0,'y':0,'w':1,'h':0.5},rotate=0)
        self.assertEqual(pixels(files()[0])[0].size,(200,100))
        edit(rotate=90,flip_h=True,brightness=1.2,contrast=1.1,saturation=0.5)
        img,_=pixels(files()[0]);self.assertEqual(img.size,(100,200))
        r,g,b=img.getpixel((50,100));self.assertTrue(34<r<46 and 140<b<165,f'brilho, contraste e cor reduzida aproximam os canais: {(r,g,b)}')

        # Giro: o lado esquerdo (vermelho) do original vai para cima.
        edit(restore=True)
        back=files()[0];self.assertFalse(back['edited']);self.assertEqual(pixels(back)[1],sent,'o arquivo enviado volta intacto')
        edit(rotate=90)
        img,_=pixels(files()[0]);self.assertEqual(img.size,(200,400))
        self.assertGreater(img.getpixel((100,50))[0],150);self.assertGreater(img.getpixel((100,350))[2],150)
        edit(restore=True);edit(flip_h=True)
        img,_=pixels(files()[0]);self.assertGreater(img.getpixel((50,100))[2],150);self.assertGreater(img.getpixel((350,100))[0],150)

        # Excluir a foto editada remove também o original guardado.
        import pathlib
        uploads=pathlib.Path(self.tmp.name)/'uploads'
        self.assertEqual(len([p for p in uploads.iterdir() if p.suffix=='.jpg']),2)
        call(a,'/api/delete-file',{'entry_id':eid,'file_id':fid})
        self.assertEqual([p for p in uploads.iterdir() if p.suffix=='.jpg'],[])

if __name__=='__main__':unittest.main()

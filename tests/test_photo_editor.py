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

        edit(restore=True)

        # Foco: nitidez só no objeto marcado e fundo suavizado. Imagem de teste: xadrez fino.
        board=Image.new('L',(400,200));board.putdata([90+70*((x//2+y//2)%2) for y in range(200) for x in range(400)])
        buf=io.BytesIO();board.convert('RGB').save(buf,'PNG');checker=buf.getvalue()
        def replace(client,data,name,file_id=None):return call(client,'/api/files/replace',data,{'X-Entry-Id':str(eid),'X-File-Id':str(file_id or fid),'X-File-Name':name})
        for client in (m,self.client()):
            with self.assertRaises(urllib.error.HTTPError) as ex:replace(client,checker,'xadrez.png')
            self.assertIn(ex.exception.code,(401,403))
        for data,name in ((b'nao e imagem','x.png'),(checker,'x.mp4'),(checker,'x.pdf'),(b'','x.png')):
            with self.assertRaises(urllib.error.HTTPError,msg=name) as ex:replace(a,data,name)
            self.assertEqual(ex.exception.code,400)
        with self.assertRaises(urllib.error.HTTPError) as ex:replace(a,checker,'x.png',pdf['id'])
        self.assertEqual(ex.exception.code,400)
        call(a,'/api/files/arrange',{'entry_id':eid,'cover_file_id':fid})
        order=[f['id'] for f in files()]
        replace(a,checker,'corrigida.png')
        swapped=files()[0]
        self.assertEqual((swapped['id'],swapped['name'],swapped['mime'],bool(swapped['edited'])),(fid,'foto.png','image/png',True))
        self.assertEqual([f['id'] for f in files()],order);self.assertEqual(next(e for e in call(a,'/api/state')['entries'] if e['id']==eid)['cover_file_id'],fid)
        self.assertEqual(pixels(swapped)[1],checker)
        spread=lambda img,box:(lambda v:max(v)-min(v))([img.getpixel((x,y))[0] for x in range(box[0],box[0]+12) for y in range(box[1],box[1]+12)])
        for bad in ({'x':.5,'y':.5,'r':.3,'sharpen':2,'blur':0},{'x':.5,'y':None,'r':.3,'sharpen':.5,'blur':0},{'x':.5,'y':.5,'r':0,'sharpen':.5,'blur':0},'forte',{'sharpen':.5}):
            with self.assertRaises(urllib.error.HTTPError,msg=repr(bad)) as ex:edit(focus=bad)
            self.assertEqual(ex.exception.code,400)
        edit(focus={'x':.25,'y':.5,'r':.3,'sharpen':1,'blur':1})
        img,_=pixels(files()[0]);self.assertEqual(img.size,(400,200))
        self.assertGreater(spread(img,(94,94)),75,'o objeto marcado ganha contraste local');self.assertLess(spread(img,(340,94)),30,'o fundo fica suavizado')
        # Sem objeto marcado, a nitidez vale para a foto toda.
        replace(a,checker,'corrigida.png');edit(focus={'x':None,'y':None,'r':.25,'sharpen':1,'blur':1})
        img,_=pixels(files()[0]);self.assertGreater(spread(img,(94,94)),75);self.assertGreater(spread(img,(340,94)),75)
        # Restaurar volta ao primeiro arquivo enviado, com o nome e o tipo dele.
        edit(restore=True)
        back=files()[0];self.assertEqual((back['name'],back['mime'],bool(back['edited'])),('foto.jpg','image/jpeg',False));self.assertEqual(pixels(back)[1],sent)
        edit(flip_h=True)

        # Excluir a foto editada remove também o original guardado.
        import pathlib
        uploads=pathlib.Path(self.tmp.name)/'uploads'
        self.assertEqual(len([p for p in uploads.iterdir() if p.suffix in ('.jpg','.png')]),2)
        call(a,'/api/delete-file',{'entry_id':eid,'file_id':fid})
        self.assertEqual([p for p in uploads.iterdir() if p.suffix in ('.jpg','.png')],[])

if __name__=='__main__':unittest.main()

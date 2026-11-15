import unittest,urllib.error
import test_app

class PoiAdmin(test_app.Integration):
    def test_complete_trip_and_access(self):
        call=self.call;a=self.admin;m=self.member
        call(a,'/api/setup',{'name':'Admin','email':'admin@poi.test','password':'initial123'})
        tid=call(a,'/api/state')['trip_id']
        call(a,'/api/members',{'name':'Viajante','email':'member@poi.test','password':'member123','trip_id':tid})
        call(m,'/api/login',{'email':'member@poi.test','password':'member123'})
        trip=call(a,'/api/state')['trips'][0]
        call(a,'/api/trips',{**{k:trip[k] for k in ('id','name','start','end','places','notes')},'public_diary':True,'member_ids':trip['member_ids']})

        # Memória de usuário com local livre: sem ponto cadastrado, cai em "outras memórias" da cidade.
        mine=call(m,'/api/entries',{'kind':'diary','trip_id':tid,'title':'Pausa','place':'Mirante da Tarde','start':'2026-11-03'})['id']
        call(m,'/api/upload',b'img',{'X-Entry-Id':str(mine),'X-File-Name':'a.jpg'})
        names=lambda:[p['name'] for p in call(a,'/api/state')['map']['points']]
        self.assertNotIn('Mirante da Tarde',names())

        # Só o administrador cadastra; membro e visitante, não.
        poi={'trip_id':tid,'name':'Mirante da Tarde','city':'Paris','lat':'48,8867','lng':2.3431,'text':'Vista da cidade.','aliases':'Mirante, Terraço'}
        for client in (m,self.client()):
            with self.assertRaises(urllib.error.HTTPError) as ex:call(client,'/api/pois',poi)
            self.assertIn(ex.exception.code,(401,403))
        pid=call(a,'/api/pois',poi)['id']
        state=call(a,'/api/state')
        point=next(p for p in state['map']['points'] if p.get('poi_id')==pid)
        self.assertEqual((point['kind'],point['level'],point['city'],point['lat']),('poi','attraction','Paris',48.8867))
        self.assertEqual(point['aliases'],['Mirante','Terraço']);self.assertEqual(point['text'],'Vista da cidade.')
        self.assertEqual(point['entry_ids'],[mine],'a memória do usuário passa para o novo ponto pelo nome')
        # também no mapa público
        self.assertIn('Mirante da Tarde',[p['name'] for p in call(self.client(),'/api/public/diary')['map']['points']])

        # Edição complementa o ponto; cidade nova usa coordenadas do próprio ponto.
        call(a,'/api/pois',{**poi,'id':pid,'text':'Texto melhor.','lat':48.9})
        self.assertEqual(next(p for p in call(a,'/api/state')['map']['points'] if p.get('poi_id')==pid)['text'],'Texto melhor.')
        new=call(a,'/api/pois',{'trip_id':tid,'name':'Praia do Futuro','city':'Fortaleza Norte','country':'Brasil','lat':-3.75,'lng':-38.45})['id']
        points=call(a,'/api/state')['map']['points']
        self.assertTrue(any(p['level']=='city' and p['name']=='Fortaleza Norte' and p['country']=='Brasil' for p in points))
        self.assertIn('Brasil',call(a,'/api/state')['map']['trips'][0]['countries'])

        # Validação.
        for bad in ({**poi,'name':''},{**poi,'lat':91},{**poi,'lng':'abc'},{**poi,'trip_id':9999},{**poi,'city':'Cidade Nova','country':''},{**poi,'aliases':'x'*200}):
            with self.assertRaises(urllib.error.HTTPError,msg=repr(bad)) as ex:call(a,'/api/pois',bad)
            self.assertEqual(ex.exception.code,400)
        listing=call(a,'/api/pois')
        self.assertEqual({p['id'] for p in listing['pois']},{pid,new});self.assertTrue(listing['cities'])
        with self.assertRaises(urllib.error.HTTPError):call(m,'/api/pois')
        call(a,'/api/pois/delete',{'id':new})
        self.assertNotIn('Praia do Futuro',names())

        # Mover foto para outra memória (admin); capa e ordem acompanham; membro não move.
        other=call(a,'/api/entries',{'kind':'diary','trip_id':tid,'title':'Outra','place':'Roma','start':'2026-11-04'})['id']
        call(a,'/api/upload',b'img',{'X-Entry-Id':str(other),'X-File-Name':'z.jpg'})
        entry=lambda eid:next(e for e in call(a,'/api/state')['entries'] if e['id']==eid)
        fid=entry(mine)['files'][0]['id']
        call(a,'/api/files/arrange',{'entry_id':mine,'cover_file_id':fid})
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,'/api/files/move',{'entry_id':mine,'file_id':fid,'to_entry_id':other})
        self.assertEqual(ex.exception.code,403)
        for bad in (9999,True,'x',None):
            with self.assertRaises(urllib.error.HTTPError,msg=repr(bad)):call(a,'/api/files/move',{'entry_id':mine,'file_id':fid,'to_entry_id':bad})
        call(a,'/api/files/move',{'entry_id':mine,'file_id':fid,'to_entry_id':other})
        self.assertEqual([f['name'] for f in entry(other)['files']],['z.jpg','a.jpg'])
        self.assertEqual(entry(mine)['files'],[]);self.assertIsNone(entry(mine)['cover_file_id'])
        # Excluir do site continua disponível ao administrador.
        call(a,'/api/delete-file',{'entry_id':other,'file_id':fid})
        self.assertEqual([f['name'] for f in entry(other)['files']],['z.jpg'])

if __name__=='__main__':unittest.main()

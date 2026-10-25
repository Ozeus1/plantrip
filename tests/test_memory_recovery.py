import unittest,urllib.error
import test_app

class MemoryRecovery(test_app.Integration):
    def test_complete_trip_and_access(self):
        call=self.call;a=self.admin;m=self.member;guest=self.client()
        call(a,'/api/setup',{'name':'Admin','email':'admin@recover.test','password':'initial123'})
        state=call(a,'/api/state');tid=state['trip_id'];tour=next(e for e in state['entries'] if e['kind']=='tour')
        call(a,'/api/members',{'name':'Viajante','email':'member@recover.test','password':'member123','trip_id':tid})
        call(m,'/api/login',{'email':'member@recover.test','password':'member123'})
        payload={'kind':'diary','trip_id':tid,'title':'Meu título livre','place':tour['title'],'attraction_id':tour['id'],'start':'2026-10-28T15:00','end':'2026-10-28T16:00','category':'Hotel'}
        eid=call(m,'/api/entries',payload)['id']
        post=next(e for e in call(m,'/api/state')['entries'] if e['id']==eid)
        self.assertEqual(post['attraction_id'],tour['id']);self.assertEqual(post['start'],'2026-10-28');self.assertEqual(post['end'],'');self.assertEqual(post['category'],'Memória')
        call(m,'/api/entries',{**payload,'id':eid,'attraction_id':None,'place':'Local livre'})
        post=next(e for e in call(m,'/api/state')['entries'] if e['id']==eid)
        self.assertIsNone(post['attraction_id']);self.assertEqual(post['place'],'Local livre')
        unknown=call(guest,'/api/password-requests',{'email':'unknown@recover.test'})
        known=call(guest,'/api/password-requests',{'email':'member@recover.test'})
        self.assertEqual(unknown,known)
        call(guest,'/api/password-requests',{'email':'member@recover.test'})
        requests=call(a,'/api/state')['password_requests'];self.assertEqual(len(requests),1)
        self.assertEqual(requests[0]['email'],'member@recover.test')
        self.assertEqual(call(m,'/api/state')['password_requests'],[])
        self.assertNotIn('password_requests',call(guest,'/api/state'))
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,'/api/password-requests/resolve',{'request_id':requests[0]['id']})
        self.assertEqual(ex.exception.code,403)
        generated=call(a,'/api/users/reset-password',{'user_id':requests[0]['user_id']})['password']
        self.assertEqual(call(a,'/api/state')['password_requests'],[])
        call(m,'/api/login',{'email':'member@recover.test','password':generated})
        self.assertEqual(call(m,'/api/state')['user']['role'],'member')
        call(guest,'/api/password-requests',{'email':'admin@recover.test'})
        request=call(a,'/api/state')['password_requests'][0]
        call(a,'/api/password-requests/resolve',{'request_id':request['id']})
        self.assertEqual(call(a,'/api/state')['password_requests'],[])

if __name__=='__main__':unittest.main()

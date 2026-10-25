import unittest,urllib.error
import test_app

class PasswordFlows(test_app.Integration):
    def test_complete_trip_and_access(self):
        call=self.call;a=self.admin;m=self.member;second=self.client();guest=self.client()
        call(a,'/api/setup',{'name':'Admin','email':'admin@password.test','password':'admin-initial-123'})
        tid=call(a,'/api/state')['trip_id']
        call(a,'/api/members',{'name':'Member','email':'member@password.test','password':'start123','trip_id':tid})
        for client in (m,second):call(client,'/api/login',{'email':'member@password.test','password':'start123'})
        uid=call(m,'/api/state')['user']['id'];admin_id=call(a,'/api/state')['user']['id']
        for client,path,payload,status in [
            (guest,'/api/account/password',{},401),
            (guest,'/api/users/reset-password',{'user_id':uid},401),
            (m,'/api/users/reset-password',{'user_id':admin_id},403),
            (m,'/api/account/password',{'current_password':'wrong','new_password':'changed123','confirmation':'changed123'},400),
            (m,'/api/account/password',{'current_password':'start123','new_password':'changed123','confirmation':'different'},400),
            (m,'/api/account/password',{'current_password':'start123','new_password':'123','confirmation':'123'},400),
            (a,'/api/users/reset-password',{'user_id':admin_id},400),
            (a,'/api/users/reset-password',{'user_id':999999},400),
        ]:
            with self.assertRaises(urllib.error.HTTPError) as ex:call(client,path,payload)
            self.assertEqual(ex.exception.code,status)
        self.assertIsNotNone(call(m,'/api/state')['user'])
        generated=call(a,'/api/users/reset-password',{'user_id':uid})['password']
        self.assertGreaterEqual(len(generated),12)
        for client in (m,second):self.assertIsNone(call(client,'/api/state')['user'])
        with self.assertRaises(urllib.error.HTTPError) as ex:call(m,'/api/login',{'email':'member@password.test','password':'start123'})
        self.assertEqual(ex.exception.code,401)
        for client in (m,second):call(client,'/api/login',{'email':'member@password.test','password':generated})
        call(m,'/api/account/password',{'current_password':generated,'new_password':'myNewPass987','confirmation':'myNewPass987'})
        for client in (m,second):self.assertIsNone(call(client,'/api/state')['user'])
        with self.assertRaises(urllib.error.HTTPError):call(m,'/api/login',{'email':'member@password.test','password':generated})
        call(m,'/api/login',{'email':'member@password.test','password':'myNewPass987'})
        self.assertEqual(call(m,'/api/state')['user']['id'],uid)
        self.assertEqual(call(a,'/api/state')['user']['id'],admin_id)
        with self.assertRaises(urllib.error.HTTPError):call(a,'/api/account/password',{'current_password':'admin-initial-123','new_password':'short','confirmation':'short'})
        call(a,'/api/account/password',{'current_password':'admin-initial-123','new_password':'admin-replaced-987','confirmation':'admin-replaced-987'})
        self.assertIsNone(call(a,'/api/state')['user'])
        call(a,'/api/login',{'email':'admin@password.test','password':'admin-replaced-987'})
        self.assertEqual(len(call(a,'/api/state')['users']),2)

if __name__=='__main__':unittest.main()

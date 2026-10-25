"""Importa companheiros de JSON privado via stdin, sem guardar senhas no código."""
import argparse,json,secrets,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

def import_members(records,trip_name,publish=False):
    if not isinstance(records,list) or not records:raise ValueError('Lista de usuários inválida')
    for p in records:
        if not p.get('name','').strip() or '@' not in p.get('email','') or len(p.get('password',''))<5:raise ValueError('Nome, e-mail ou senha inválidos')
    app.init()
    with app.db() as c:
        c.execute('BEGIN IMMEDIATE')
        trips=c.execute('SELECT id FROM trips WHERE name=?',(trip_name,)).fetchall()
        if len(trips)!=1:raise ValueError('A viagem deve existir e ter nome único')
        tid=trips[0][0];created=0
        for p in records:
            email=p['email'].strip().lower()
            row=c.execute('SELECT id,role FROM users WHERE email=?',(email,)).fetchone()
            if row:
                if row['role']!='member':raise ValueError('Um e-mail informado pertence a um administrador')
                uid=row['id']
            else:
                salt=secrets.token_hex(16)
                uid=c.execute('INSERT INTO users(name,email,password,salt,role) VALUES(?,?,?,?,?)',(p['name'].strip(),email,app.password(p['password'],salt),salt,'member')).lastrowid;created+=1
            c.execute('INSERT OR IGNORE INTO trip_members VALUES(?,?)',(tid,uid))
        if publish:c.execute('UPDATE trips SET public_diary=1 WHERE id=?',(tid,))
        return created,len(records)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--trip',required=True);parser.add_argument('--publish-diary',action='store_true');args=parser.parse_args()
    try:
        created,total=import_members(json.load(sys.stdin),args.trip,args.publish_diary)
        print(f'{created} usuários criados; {total} participantes vinculados. Senhas de contas existentes preservadas.')
    except (ValueError,KeyError) as e:raise SystemExit(str(e))

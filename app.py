import os, json, sqlite3, secrets, hashlib, hmac, mimetypes, re
from pathlib import Path
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).parent
DATA = Path(os.environ.get('DATA_DIR', ROOT / 'data'))
DATA.mkdir(parents=True, exist_ok=True)
(DATA / 'uploads').mkdir(exist_ok=True)

class Connection(sqlite3.Connection):
    def __exit__(self, *args):
        try:return super().__exit__(*args)
        finally:self.close()

def db():
    c = sqlite3.connect(DATA / 'plantrip.db',factory=Connection)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def password(value, salt):
    return hashlib.pbkdf2_hmac('sha256', value.encode(), bytes.fromhex(salt), 200000).hex()

def init():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT,salt TEXT,role TEXT);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER REFERENCES users(id),expires TEXT);
        CREATE TABLE IF NOT EXISTS entries(id INTEGER PRIMARY KEY,kind TEXT,title TEXT,place TEXT,start TEXT,end TEXT,description TEXT,category TEXT,user_id INTEGER REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS files(id INTEGER PRIMARY KEY,entry_id INTEGER REFERENCES entries(id) ON DELETE CASCADE,name TEXT,path TEXT,mime TEXT);
        CREATE TABLE IF NOT EXISTS comments(id INTEGER PRIMARY KEY,entry_id INTEGER REFERENCES entries(id) ON DELETE CASCADE,user_id INTEGER REFERENCES users(id),body TEXT,created TEXT);
        ''')
        c.executescript('''
        CREATE TABLE IF NOT EXISTS trips(id INTEGER PRIMARY KEY,name TEXT NOT NULL,start TEXT NOT NULL,end TEXT NOT NULL,places TEXT NOT NULL,notes TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS trip_members(trip_id INTEGER REFERENCES trips(id) ON DELETE CASCADE,user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,PRIMARY KEY(trip_id,user_id));
        CREATE TABLE IF NOT EXISTS migrations(name TEXT PRIMARY KEY);
        ''')
        if 'trip_id' not in {r['name'] for r in c.execute('PRAGMA table_info(entries)')}:
            c.execute('ALTER TABLE entries ADD COLUMN trip_id INTEGER REFERENCES trips(id)')
        if 'guide_key' not in {r['name'] for r in c.execute('PRAGMA table_info(entries)')}:
            c.execute('ALTER TABLE entries ADD COLUMN guide_key TEXT')
        if 'attraction_id' not in {r['name'] for r in c.execute('PRAGMA table_info(entries)')}:
            c.execute('ALTER TABLE entries ADD COLUMN attraction_id INTEGER REFERENCES entries(id) ON DELETE SET NULL')
        if 'sort_order' not in {r['name'] for r in c.execute('PRAGMA table_info(entries)')}:
            c.execute('ALTER TABLE entries ADD COLUMN sort_order INTEGER')
        if 'public_diary' not in {r['name'] for r in c.execute('PRAGMA table_info(trips)')}:
            c.execute('ALTER TABLE trips ADD COLUMN public_diary INTEGER NOT NULL DEFAULT 0')
        from europe import seed
        seed(c)
        from attractions import attach_guides
        attach_guides(c)

def allowed(c,u,trip_id):
    return bool(c.execute('SELECT 1 FROM trips WHERE id=?',(trip_id,)).fetchone()) and (u['role']=='admin' or bool(c.execute('SELECT 1 FROM trip_members WHERE trip_id=? AND user_id=?',(trip_id,u['id'])).fetchone()))

def available_trips(c,u):
    rows=c.execute('SELECT * FROM trips ORDER BY start,id') if u['role']=='admin' else c.execute('SELECT t.* FROM trips t JOIN trip_members m ON m.trip_id=t.id WHERE m.user_id=? ORDER BY t.start,t.id',(u['id'],))
    trips=[dict(r) for r in rows]
    for trip in trips:trip['member_ids']=[r[0] for r in c.execute('SELECT user_id FROM trip_members WHERE trip_id=?',(trip['id'],))]
    return trips

class Handler(BaseHTTPRequestHandler):
    def respond(self, data, status=200):
        body=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(body)

    def user(self,c):
        cookie=SimpleCookie(); cookie.load(self.headers.get('Cookie',''))
        token=cookie.get('session')
        return c.execute('SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=? AND s.expires>?',(token.value if token else '',datetime.now(timezone.utc).isoformat())).fetchone()

    def do_GET(self):
        path=self.path.split('?')[0]
        with db() as c:
            u=self.user(c)
            if path=='/api/public/diary':
                trips=[dict(r) for r in c.execute('SELECT id,name FROM trips WHERE public_diary=1 ORDER BY start,id')]
                entries=[dict(r) for r in c.execute("SELECT e.id,e.trip_id,e.title,e.place,e.start,e.description,u.name author FROM entries e JOIN trips t ON t.id=e.trip_id JOIN users u ON u.id=e.user_id WHERE e.kind='diary' AND t.public_diary=1 ORDER BY e.start DESC,e.id DESC")]
                for e in entries:
                    e['files']=[dict(r) for r in c.execute("SELECT id,name,mime FROM files WHERE entry_id=? AND (mime LIKE 'image/%' OR mime LIKE 'video/%')",(e['id'],))]
                    e['comments']=[dict(r) for r in c.execute('SELECT u.name author,c.body,c.created FROM comments c JOIN users u ON u.id=c.user_id WHERE c.entry_id=? ORDER BY c.id',(e['id'],))]
                return self.respond({'trips':trips,'entries':entries})
            if path=='/api/state':
                if not u:
                    return self.respond({'user':None,'setup':os.environ.get('ALLOW_SETUP','1')=='1' and c.execute('SELECT count(*) FROM users').fetchone()[0]==0})
                trips=available_trips(c,u)
                requested=parse_qs(urlsplit(self.path).query).get('trip_id',[None])[0]
                trip_id=next((t['id'] for t in trips if str(t['id'])==requested),None) if requested else (trips[0]['id'] if trips else None)
                if requested and trip_id is None:return self.respond({'error':'Sem acesso a esta viagem'},403)
                entries=[dict(r) for r in c.execute('SELECT e.*,u.name author FROM entries e JOIN users u ON u.id=e.user_id WHERE e.trip_id=? ORDER BY CASE WHEN sort_order IS NULL THEN 1 ELSE 0 END,sort_order,start,id',(trip_id,))]
                for e in entries:
                    from attractions import preview
                    e['guide']=preview(e)
                    e['files']=[dict(r) for r in c.execute('SELECT id,name,mime FROM files WHERE entry_id=?',(e['id'],))]
                    e['comments']=[dict(r) for r in c.execute('SELECT c.*,u.name author FROM comments c JOIN users u ON u.id=c.user_id WHERE entry_id=? ORDER BY c.id',(e['id'],))]
                members=[dict(r) for r in c.execute('SELECT id,name,role FROM users WHERE id IN (SELECT user_id FROM trip_members WHERE trip_id=?)',(trip_id,))]
                users=[dict(r) for r in c.execute('SELECT id,name,email,role FROM users ORDER BY name')] if u['role']=='admin' else []
                return self.respond({'user':{k:u[k] for k in ('id','name','role')},'entries':entries,'members':members,'users':users,'trips':trips,'trip_id':trip_id})
            if path.startswith('/api/attractions/'):
                if not u:return self.respond({'error':'Faça login para consultar esta atração'},401)
                eid=path.rsplit('/',1)[-1]
                entry=c.execute("SELECT e.*,u.name author FROM entries e JOIN users u ON u.id=e.user_id WHERE e.id=? AND e.kind='tour'",(eid,)).fetchone()
                if not entry:return self.respond({'error':'Passeio não encontrado'},404)
                if not allowed(c,u,entry['trip_id']):return self.respond({'error':'Sem acesso a esta viagem'},403)
                e=dict(entry)
                e['files']=[dict(r) for r in c.execute('SELECT id,name,mime FROM files WHERE entry_id=?',(e['id'],))]
                e['comments']=[dict(r) for r in c.execute('SELECT c.*,u.name author FROM comments c JOIN users u ON u.id=c.user_id WHERE entry_id=? ORDER BY c.id',(e['id'],))]
                from attractions import guide_for
                return self.respond({'entry':e,'guide':guide_for(entry)})
            if path.startswith('/media/'):
                f=c.execute('SELECT * FROM files WHERE id=?',(path.rsplit('/',1)[-1],)).fetchone()
                if not f:return self.respond({'error':'Arquivo não encontrado'},404)
                entry=c.execute('SELECT e.trip_id,e.kind,t.public_diary FROM entries e JOIN trips t ON t.id=e.trip_id WHERE e.id=?',(f['entry_id'],)).fetchone()
                public=bool(entry and entry['kind']=='diary' and entry['public_diary'] and f['mime'].startswith(('image/','video/')))
                if not public and not u:return self.respond({'error':'Entre para acessar os arquivos.'},401)
                if not public and (not entry or not allowed(c,u,entry['trip_id'])):return self.respond({'error':'Sem acesso a esta viagem'},403)
                target=DATA/'uploads'/f['path']; mime=f['mime']
            else:
                target=ROOT/'static'/('index.html' if path in ('/','/diary') or re.fullmatch(r'/attractions/\d+/?',path) else path.lstrip('/'))
                if not target.resolve().is_relative_to((ROOT/'static').resolve()):return self.respond({'error':'Inválido'},404)
                mime=mimetypes.guess_type(str(target))[0] or 'application/octet-stream'
            if not target.is_file():return self.respond({'error':'Não encontrado'},404)
            body=target.read_bytes(); self.send_response(200); self.send_header('Content-Type',mime)
            if path.startswith('/media/'):self.send_header('Cache-Control','private, no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_POST(self):
        try:
            origin=self.headers.get('Origin')
            if origin and origin.split('://',1)[-1]!=self.headers.get('Host'):return self.respond({'error':'Origem inválida'},403)
            size=int(self.headers.get('Content-Length',0))
            if size>100*1024*1024:return self.respond({'error':'Limite de 100 MB por arquivo'},413)
            raw=self.rfile.read(size)
            payload=json.loads(raw) if self.headers.get('Content-Type','').startswith('application/json') else {}
            with db() as c:
                u=self.user(c); path=self.path
                if path in ('/api/setup','/api/login'):
                    if path.endswith('setup'):
                        if os.environ.get('ALLOW_SETUP','1')!='1':return self.respond({'error':'Cadastro inicial desabilitado. O administrador deve ser criado no servidor.'},403)
                        if c.execute('SELECT count(*) FROM users').fetchone()[0]:return self.respond({'error':'Administrador já configurado'},403)
                        self.add_user(c,payload,'admin')
                        from europe import seed
                        seed(c)
                        from attractions import attach_guides
                        attach_guides(c)
                    row=c.execute('SELECT * FROM users WHERE email=?',(payload.get('email','').strip().lower(),)).fetchone()
                    if not row or not hmac.compare_digest(password(payload.get('password',''),row['salt']),row['password']):return self.respond({'error':'E-mail ou senha inválidos'},401)
                    token=secrets.token_hex(32)
                    c.execute('INSERT INTO sessions VALUES(?,?,?)',(token,row['id'],(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()))
                    c.commit(); self.send_response(200)
                    self.send_header('Set-Cookie',f'session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800'+('; Secure' if os.environ.get('COOKIE_SECURE')=='1' else ''))
                    self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(b'{}'); return
                if not u:return self.respond({'error':'Faça login'},401)
                if path=='/api/logout':
                    cookie=SimpleCookie(); cookie.load(self.headers.get('Cookie','')); c.execute('DELETE FROM sessions WHERE token=?',(cookie['session'].value,)); return self.respond({'ok':True})
                if path=='/api/members':
                    if u['role']!='admin':return self.respond({'error':'Apenas administrador'},403)
                    uid=self.add_user(c,payload,'member')
                    if payload.get('trip_id'):
                        if not allowed(c,u,payload['trip_id']):raise ValueError('Viagem inexistente')
                        c.execute('INSERT INTO trip_members VALUES(?,?)',(payload['trip_id'],uid))
                    return self.respond({'ok':True})
                if path=='/api/users':
                    if u['role']!='admin':return self.respond({'error':'Apenas administrador'},403)
                    uid=payload.get('id')
                    if not uid:return self.respond({'id':self.add_user(c,payload,'member')})
                    if not c.execute('SELECT 1 FROM users WHERE id=?',(uid,)).fetchone():raise ValueError('Usuário inexistente')
                    name=payload.get('name','').strip(); email=payload.get('email','').strip().lower()
                    if not name or '@' not in email:raise ValueError('Informe nome e e-mail válidos')
                    c.execute('UPDATE users SET name=?,email=? WHERE id=?',(name,email,uid))
                    return self.respond({'id':uid})
                if path=='/api/trips':
                    if u['role']!='admin':return self.respond({'error':'Apenas administrador'},403)
                    tid=payload.get('id'); name=payload.get('name','').strip()
                    start=payload.get('start',''); end=payload.get('end','')
                    datetime.strptime(start,'%Y-%m-%d'); datetime.strptime(end,'%Y-%m-%d')
                    if not name or end<start:raise ValueError('Informe nome e período válidos')
                    members=payload.get('member_ids',[])
                    if not isinstance(members,list):raise ValueError('Participantes inválidos')
                    members=set(int(x) for x in members)
                    if any(not c.execute('SELECT 1 FROM users WHERE id=?',(uid,)).fetchone() for uid in members):raise ValueError('Participante inexistente')
                    values=(name,start,end,payload.get('places','').strip(),payload.get('notes','').strip())
                    if tid:
                        if not c.execute('SELECT 1 FROM trips WHERE id=?',(tid,)).fetchone():raise ValueError('Viagem inexistente')
                        c.execute('UPDATE trips SET name=?,start=?,end=?,places=?,notes=? WHERE id=?',values+(tid,))
                    else:tid=c.execute('INSERT INTO trips(name,start,end,places,notes) VALUES(?,?,?,?,?)',values).lastrowid
                    if 'public_diary' in payload:
                        if type(payload['public_diary']) is not bool:raise ValueError('Visibilidade do diário inválida')
                        c.execute('UPDATE trips SET public_diary=? WHERE id=?',(int(payload['public_diary']),tid))
                    c.execute('DELETE FROM trip_members WHERE trip_id=?',(tid,))
                    c.executemany('INSERT INTO trip_members VALUES(?,?)',[(tid,uid) for uid in members])
                    return self.respond({'id':tid})
                if path=='/api/entries/reorder':
                    if u['role']!='admin':return self.respond({'error':'Apenas o administrador pode alterar a ordem'},403)
                    tid=payload.get('trip_id');kind=payload.get('kind')
                    if kind not in ('logistics','tour'):raise ValueError('Módulo inválido para ordenação')
                    if not allowed(c,u,tid):return self.respond({'error':'Viagem inexistente'},404)
                    c.execute('BEGIN IMMEDIATE')
                    if payload.get('reset') is True:
                        c.execute('UPDATE entries SET sort_order=NULL WHERE trip_id=? AND kind=?',(tid,kind))
                    else:
                        ids=payload.get('entry_ids')
                        if not isinstance(ids,list) or not ids or any(type(i) is not int for i in ids) or len(set(ids))!=len(ids):raise ValueError('Lista de etapas inválida')
                        expected={r[0] for r in c.execute('SELECT id FROM entries WHERE trip_id=? AND kind=?',(tid,kind))}
                        if set(ids)!=expected:return self.respond({'error':'A lista mudou. Atualize a página e tente novamente.'},409)
                        c.executemany('UPDATE entries SET sort_order=? WHERE id=? AND trip_id=? AND kind=?',[(position,eid,tid,kind) for position,eid in enumerate(ids)])
                    return self.respond({'ok':True})
                if path=='/api/entries':
                    kind=payload.get('kind'); eid=payload.get('id')
                    if kind not in ('logistics','tour','diary'):raise ValueError('Tipo inválido')
                    old=c.execute('SELECT * FROM entries WHERE id=?',(eid,)).fetchone() if eid else None
                    tid=old['trip_id'] if old else payload.get('trip_id')
                    if not tid:raise ValueError('Selecione uma viagem')
                    if not allowed(c,u,tid):return self.respond({'error':'Sem acesso a esta viagem'},403)
                    if (kind!='diary' and u['role']!='admin') or (old and u['role']!='admin' and (old['user_id']!=u['id'] or old['kind']!='diary')):return self.respond({'error':'Sem permissão'},403)
                    title=payload.get('title','').strip()
                    if not title:raise ValueError('Informe o título')
                    start=payload.get('start',''); end=payload.get('end','')
                    if start:datetime.fromisoformat(start)
                    if end and (not start or datetime.fromisoformat(end)<datetime.fromisoformat(start)):raise ValueError('O término deve ser posterior ao início')
                    values=(kind,title,payload.get('place',''),start,end,payload.get('description',''),payload.get('category',''))
                    attraction_id=payload.get('attraction_id') or (old['attraction_id'] if old else None)
                    if attraction_id:
                        parent=c.execute("SELECT trip_id FROM entries WHERE id=? AND kind='tour'",(attraction_id,)).fetchone()
                        if kind!='diary' or not parent or str(parent['trip_id'])!=str(tid):raise ValueError('Atração inválida para esta memória')
                    if eid:
                        if not old:raise ValueError('Etapa inexistente')
                        c.execute('UPDATE entries SET kind=?,title=?,place=?,start=?,end=?,description=?,category=? WHERE id=?',values+(eid,))
                    else:eid=c.execute('INSERT INTO entries(kind,title,place,start,end,description,category,user_id,trip_id) VALUES(?,?,?,?,?,?,?,?,?)',values+(u['id'],tid)).lastrowid
                    c.execute('UPDATE entries SET attraction_id=? WHERE id=?',(attraction_id,eid))
                    return self.respond({'id':eid})
                eid=int(self.headers.get('X-Entry-Id',0) if path=='/api/upload' else payload.get('entry_id',0))
                entry=c.execute('SELECT * FROM entries WHERE id=?',(eid,)).fetchone()
                if not entry:raise ValueError('Etapa inexistente')
                if not allowed(c,u,entry['trip_id']):return self.respond({'error':'Sem acesso a esta viagem'},403)
                if path=='/api/comments':
                    body=payload.get('body','').strip()
                    if not body or len(body)>4000:raise ValueError('Comentário deve ter entre 1 e 4000 caracteres')
                    c.execute('INSERT INTO comments(entry_id,user_id,body,created) VALUES(?,?,?,?)',(eid,u['id'],body,datetime.now(timezone.utc).isoformat())); return self.respond({'ok':True})
                if u['role']!='admin' and (entry['user_id']!=u['id'] or entry['kind']!='diary'):return self.respond({'error':'Sem permissão'},403)
                if path=='/api/delete':
                    files=c.execute('SELECT path FROM files WHERE entry_id=?',(eid,)).fetchall()
                    c.execute('DELETE FROM entries WHERE id=?',(eid,))
                    for f in files:(DATA/'uploads'/f['path']).unlink(missing_ok=True)
                    return self.respond({'ok':True})
                if path=='/api/delete-file':
                    f=c.execute('SELECT id,path FROM files WHERE id=? AND entry_id=?',(int(payload.get('file_id',0)),eid)).fetchone()
                    if not f:raise ValueError('Arquivo inexistente')
                    c.execute('DELETE FROM files WHERE id=?',(f['id'],))
                    (DATA/'uploads'/f['path']).unlink(missing_ok=True)
                    return self.respond({'ok':True})
                if path=='/api/upload':
                    name=Path(self.headers.get('X-File-Name','arquivo')).name
                    from urllib.parse import unquote
                    name=unquote(name); ext=Path(name).suffix.lower()
                    mime_types={'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.gif':'image/gif','.mp4':'video/mp4','.webm':'video/webm','.mov':'video/quicktime','.pdf':'application/pdf'}
                    if ext not in mime_types:raise ValueError('Use imagem, vídeo MP4/WebM/MOV ou PDF')
                    filename=secrets.token_hex(24)+ext; (DATA/'uploads'/filename).write_bytes(raw)
                    c.execute('INSERT INTO files(entry_id,name,path,mime) VALUES(?,?,?,?)',(eid,name,filename,mime_types[ext])); return self.respond({'ok':True})
                return self.respond({'error':'Rota inexistente'},404)
        except (ValueError,KeyError,sqlite3.IntegrityError) as ex:self.respond({'error':str(ex) if not isinstance(ex,sqlite3.IntegrityError) else 'Este e-mail já está cadastrado'},400)

    def add_user(self,c,p,role):
        minimum=8 if role=='admin' else 5
        if len(p.get('password',''))<minimum:raise ValueError(f'Use uma senha com pelo menos {minimum} caracteres')
        if not p.get('name','').strip() or '@' not in p.get('email',''):raise ValueError('Informe nome e e-mail válidos')
        salt=secrets.token_hex(16)
        return c.execute('INSERT INTO users(name,email,password,salt,role) VALUES(?,?,?,?,?)',(p['name'].strip(),p['email'].strip().lower(),password(p['password'],salt),salt,role)).lastrowid

if __name__=='__main__':
    init()
    print('Plantrip disponível em http://localhost:'+os.environ.get('PORT','8000'),flush=True)
    ThreadingHTTPServer((os.environ.get('HOST','127.0.0.1'),int(os.environ.get('PORT','8000'))),Handler).serve_forever()

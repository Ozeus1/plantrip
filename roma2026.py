"""Atualização única do roteiro informado pelo grupo, preservando vínculos e anexos."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

MARKER = 'europa-roma-toscana-202610-v1'

def apply(c):
    apply_file(c,'roma2026.json',MARKER,'roma')

def apply_file(c,filename,marker,backup_prefix):
    if c.execute('SELECT 1 FROM migrations WHERE name=?',(marker,)).fetchone():return
    trip=c.execute("SELECT id FROM trips WHERE name='Europa' AND start='2026-10-27' ORDER BY id LIMIT 1").fetchone()
    admin=c.execute("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1").fetchone()
    if not trip or not admin:return
    database=next((r[2] for r in c.execute('PRAGMA database_list') if r[1]=='main'),None)
    if database:
        backup=Path(database).with_name('backup-before-'+backup_prefix+'-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.db')
        with closing(sqlite3.connect(database)) as source,closing(sqlite3.connect(backup)) as target:source.backup(target)
    data=json.loads((Path(__file__).parent/filename).read_text(encoding='utf-8'))
    for item in data['stages']:
        row=c.execute("SELECT id,description FROM entries WHERE trip_id=? AND kind='tour' AND (guide_key=? OR title=?) ORDER BY id LIMIT 1",(trip[0],item['key'],item['old_title'])).fetchone()
        description=item['description']+'\n\n'+data['common']
        if row:
            # Preserve the original planning notes as well as the existing entry ID.
            if row[1]:description+='\n\nRegistro anterior do planejamento (substituído pelo roteiro acima):\n'+row[1]
            c.execute('UPDATE entries SET title=?,place=?,start=?,end=?,description=?,guide_key=?,sort_order=NULL WHERE id=?',(item['title'],item['place'],item['start'],item['end'],description,item['key'],row[0]))
        else:
            c.execute('INSERT INTO entries(kind,title,place,start,end,description,category,user_id,trip_id,guide_key) VALUES(?,?,?,?,?,?,?,?,?,?)',('tour',item['title'],item['place'],item['start'],item['end'],description,'Passeio',admin[0],trip[0],item['key']))
    c.execute('INSERT INTO migrations(name) VALUES(?)',(marker,))

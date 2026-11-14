"""Localização geográfica das memórias públicas: viagem → cidade → atração."""
import json, re, unicodedata
from pathlib import Path
from attractions import catalog

def _places():
    return json.loads((Path(__file__).parent/'places.json').read_text(encoding='utf-8'))

def norm(value):
    text=unicodedata.normalize('NFD',str(value or '')).lower().replace('’',"'")
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',''.join(ch for ch in text if not unicodedata.combining(ch)))).strip()

def _city_for(places,label):
    """'Reims — Champagne' → Reims; texto livre que contém o nome/alias da cidade."""
    text=norm(str(label or '').split('—')[0])
    for name,city in places['cities'].items():
        if text==norm(name) or text in map(norm,city['aliases']):return name
    return None

def _alias_city(places,text):
    words=f' {norm(text)} '
    return next((name for name,city in places['cities'].items() if any(f' {norm(a)} ' in words for a in city['aliases'])),None)

def _match_attraction(candidates,text):
    """Igualdade vale mais que contido; o trecho comparado precisa ter ao menos 5 caracteres."""
    needle=norm(text)
    if len(needle)<5:return None
    best=None
    for key,names in candidates:
        for name in names:
            if name==needle:score=3
            elif len(name)>=5 and (name in needle or needle in name):score=1+min(len(name),len(needle))/max(len(name),len(needle))
            else:continue
            if not best or score>best[0]:best=(score,key)
    return best[1] if best else None

def build_map(c,entries):
    """Agrupa as memórias públicas (`entries`, já filtradas) em pontos com coordenadas."""
    places=_places();guides=catalog()
    trips={}
    for t in c.execute('SELECT id,name FROM trips WHERE public_diary=1 ORDER BY start,id'):trips[t['id']]={'id':t['id'],'name':t['name']}
    tours=[dict(r) for r in c.execute("SELECT e.id,e.trip_id,e.place,e.guide_key FROM entries e JOIN trips t ON t.id=e.trip_id WHERE e.kind='tour' AND t.public_diary=1 ORDER BY e.start,e.id")]
    spots={};by_tour={};candidates={}
    for t in tours:
        g=guides.get(t['guide_key']);coords=places['guides'].get(t['guide_key'])
        city=_city_for(places,t['place'] or (g or {}).get('city'))
        if not g or not coords or not city:continue
        key=(t['trip_id'],t['guide_key'])
        spots.setdefault(key,{'id':f"a-{t['trip_id']}-{t['guide_key']}",'level':'attraction','trip_id':t['trip_id'],'city':city,'name':g['title'].split(' — ')[0],'lat':coords[0],'lng':coords[1],'entry_ids':[]})
        by_tour[t['id']]=key
        candidates.setdefault(t['trip_id'],[]).append((key,[norm(g['title']),norm(g['title'].split(' — ')[0])]))
    general={}
    for e in entries:
        tid=e['trip_id'];key=None;city=None
        if tid not in trips:continue
        text=e.get('place') or ''
        city=_city_for(places,text)
        if e.get('attraction_id') in by_tour:key=by_tour[e['attraction_id']]
        elif not city:key=_match_attraction(candidates.get(tid,[]),text) or _match_attraction(candidates.get(tid,[]),e.get('title'))
        if key:spots[key]['entry_ids'].append(e['id']);continue
        city=city or _alias_city(places,text) or _alias_city(places,e.get('title'))
        if city:general.setdefault((tid,city),[]).append(e['id'])
    attractions=[s for s in spots.values() if s['entry_ids']]
    for (tid,city),ids in general.items():
        attractions.append({'id':f'g-{tid}-{city}','level':'attraction','trip_id':tid,'city':city,'name':f'{city} · outras memórias','lat':places['cities'][city]['lat'],'lng':places['cities'][city]['lng'],'entry_ids':ids})
    cities={}
    for a in attractions:
        item=cities.setdefault((a['trip_id'],a['city']),{'id':f"c-{a['trip_id']}-{a['city']}",'level':'city','trip_id':a['trip_id'],'name':a['city'],'lat':places['cities'][a['city']]['lat'],'lng':places['cities'][a['city']]['lng'],'entry_ids':[]})
        item['entry_ids'].extend(a['entry_ids'])
    trip_points=[]
    for tid,t in trips.items():
        mine=[x for x in cities.values() if x['trip_id']==tid]
        if not mine:continue
        ids=[i for x in mine for i in x['entry_ids']]
        trip_points.append({'id':f't-{tid}','level':'trip','trip_id':tid,'name':t['name'],'lat':sum(x['lat'] for x in mine)/len(mine),'lng':sum(x['lng'] for x in mine)/len(mine),'entry_ids':ids,'cities':[x['name'] for x in mine]})
    located={i for a in attractions for i in a['entry_ids']}
    return {'points':trip_points+list(cities.values())+attractions,'unlocated':[e['id'] for e in entries if e['id'] not in located]}

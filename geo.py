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

def _match_poi(pois,text):
    words=f' {norm(text)} '
    return next((p for p in pois if any(f' {norm(a)} ' in words for a in p.get('aliases',[]))),None)

def _route(places,text):
    """Cidades do campo 'places' da viagem (Roma → Paris → ...), na ordem, sem repetição."""
    out=[]
    for part in re.split(r'→|->|>',text or ''):
        city=_city_for(places,part)
        if city and city not in out:out.append(city)
    return out

def build_map(c,entries,trip_ids=None,detailed=False):
    """Agrupa as memórias (`entries`, já filtradas) em pontos com coordenadas.

    Sem `trip_ids`, considera as viagens com diário público. Com `detailed`, inclui também os
    passeios agendados (mesmo sem fotos) e o roteiro; é usado somente na área logada.
    """
    places=_places();guides=catalog()
    if trip_ids is None:rows=c.execute('SELECT id,name,start,end,places FROM trips WHERE public_diary=1 ORDER BY start,id').fetchall()
    else:rows=c.execute(f"SELECT id,name,start,end,places FROM trips WHERE id IN ({','.join('?'*len(trip_ids))}) ORDER BY start,id",tuple(trip_ids)).fetchall() if trip_ids else []
    trips={r['id']:dict(r) for r in rows}
    if not trips:return {'points':[],'trips':[],'unlocated':[]}
    marks=','.join('?'*len(trips))
    tours=[dict(r) for r in c.execute(f"SELECT id,trip_id,place,guide_key,start FROM entries WHERE kind='tour' AND trip_id IN ({marks}) ORDER BY start,id",tuple(trips))]
    extras={tid:places.get('trips',{}).get(t['name'],{}) for tid,t in trips.items()}
    spots={};by_tour={};candidates={}
    for t in tours:
        g=guides.get(t['guide_key']);coords=places['guides'].get(t['guide_key'])
        city=_city_for(places,t['place'] or (g or {}).get('city'))
        if not g or not coords or not city:continue
        key=(t['trip_id'],t['guide_key'])
        spot=spots.setdefault(key,{'id':f"a-{t['trip_id']}-{t['guide_key']}",'level':'attraction','trip_id':t['trip_id'],'city':city,'name':g['title'].split(' — ')[0],'lat':coords[0],'lng':coords[1],'entry_ids':[],'scheduled':False})
        spot['scheduled']=spot['scheduled'] or bool(t['start'])
        by_tour[t['id']]=key
        candidates.setdefault(t['trip_id'],[]).append((key,[norm(g['title']),norm(g['title'].split(' — ')[0])]))
    pois={}
    origins={}
    for tid,ex in extras.items():
        for p in ex.get('interest',[]):
            pois[(tid,p['id'])]={'id':f"p-{tid}-{p['id']}",'level':'attraction','kind':'poi','trip_id':tid,'city':p['city'],'name':p['name'],'lat':p['lat'],'lng':p['lng'],'text':p.get('text',''),'entry_ids':[],'always':True}
        if ex.get('origin'):
            name=ex['origin']['city'];city=places['cities'][name]
            origins[tid]={'id':f'o-{tid}','level':'origin','trip_id':tid,'city':name,'name':name,'country':city['country'],'lat':city['lat'],'lng':city['lng'],'text':ex['origin'].get('text',''),'entry_ids':[],'always':True}
    general={}
    for e in entries:
        tid=e['trip_id']
        if tid not in trips:continue
        text=e.get('place') or '';title=e.get('title');city=_city_for(places,text);key=None
        if e.get('attraction_id') in by_tour:key=by_tour[e['attraction_id']]
        else:
            poi=next((pois[(tid,p['id'])] for p in extras[tid].get('interest',[]) if _match_poi([p],text) or _match_poi([p],title)),None)
            if poi:poi['entry_ids'].append(e['id']);continue
            if not city:key=_match_attraction(candidates.get(tid,[]),text) or _match_attraction(candidates.get(tid,[]),title)
        if key:spots[key]['entry_ids'].append(e['id']);continue
        city=city or _alias_city(places,text) or _alias_city(places,title)
        if not city:continue
        if tid in origins and city==origins[tid]['city']:origins[tid]['entry_ids'].append(e['id']);continue
        general.setdefault((tid,city),[]).append(e['id'])
    attractions=[]
    for s in spots.values():
        if s['entry_ids'] or (detailed and s['scheduled']):
            s['always']=bool(detailed and s['scheduled']);attractions.append(s)
    for (tid,city),ids in general.items():
        attractions.append({'id':f'g-{tid}-{city}','level':'attraction','trip_id':tid,'city':city,'name':f'{city} · outras memórias','lat':places['cities'][city]['lat'],'lng':places['cities'][city]['lng'],'entry_ids':ids})
    attractions.extend(pois.values())
    cities={}
    for a in attractions:
        info=places['cities'][a['city']]
        item=cities.setdefault((a['trip_id'],a['city']),{'id':f"c-{a['trip_id']}-{a['city']}",'level':'city','trip_id':a['trip_id'],'name':a['city'],'country':info['country'],'lat':info['lat'],'lng':info['lng'],'entry_ids':[]})
        item['entry_ids'].extend(a['entry_ids']);item['always']=item.get('always',False) or bool(a.get('always'))
    trip_points=[];meta=[]
    for tid,t in trips.items():
        mine=[x for x in cities.values() if x['trip_id']==tid]
        route=_route(places,t['places']) if detailed else []
        countries=[]
        for name in route+[x['name'] for x in mine]:
            country=places['cities'][name]['country']
            if country not in countries:countries.append(country)
        origin=origins.get(tid)
        meta.append({'id':tid,'name':t['name'],'start':t['start'],'end':t['end'],'route':route,'countries':countries,'origin':{'name':origin['name'],'country':origin['country']} if origin else None})
        if not mine:continue
        trip_points.append({'id':f't-{tid}','level':'trip','trip_id':tid,'name':t['name'],'lat':sum(x['lat'] for x in mine)/len(mine),'lng':sum(x['lng'] for x in mine)/len(mine),'entry_ids':[i for x in mine for i in x['entry_ids']],'cities':[x['name'] for x in mine],'always':any(x.get('always') for x in mine)})
    located={i for a in attractions for i in a['entry_ids']}|{i for o in origins.values() for i in o['entry_ids']}
    return {'points':trip_points+list(cities.values())+attractions+list(origins.values()),'trips':meta,'unlocated':[e['id'] for e in entries if e['id'] not in located]}

"""Fotografias do Commons com autoria, licença e proveniência preservadas."""
import concurrent.futures,hashlib,html,json,re,time,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'static'/'guide-photos'
HEADERS={'User-Agent':'Mozilla/5.0 Plantrip/1.0 (travel guide; Wikimedia attribution retained)'}
def request(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=30) as r:return r.read()
        except Exception:
            if attempt==2:raise
            time.sleep(1+attempt)
def clean(x):return html.unescape(re.sub('<[^>]*>','',x or '')).strip()
def fetch(query,title):
    args=dict(action='query',generator='search',gsrsearch=query+' filetype:bitmap',gsrnamespace=6,gsrlimit=12,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=1000,format='json')
    result=json.loads(request('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(args)))
    pages=sorted(result.get('query',{}).get('pages',{}).values(),key=lambda x:x.get('index',999))
    photos=[]
    for page in pages:
        if len(photos)==2:break
        info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{})
        license=clean(meta.get('LicenseShortName',{}).get('value',''))
        author=clean(meta.get('Artist',{}).get('value',''))
        if not author or not ('CC' in license or 'Public domain' in license or license=='PDM'):continue
        url=info.get('thumburl',info.get('url',''))
        if not re.search(r'\.(?:jpg|jpeg|png)(?:$|\?)',url,re.I):continue
        name=hashlib.sha256(info['url'].encode()).hexdigest()[:20]+Path(urllib.parse.urlsplit(url).path).suffix.lower()
        target=DEST/name
        if not target.exists():
            blob=request(url)
            if not (blob.startswith(b'\xff\xd8') or blob.startswith(b'\x89PNG')):continue
            target.write_bytes(blob)
        source=info.get('descriptionurl','https://commons.wikimedia.org/wiki/'+urllib.parse.quote(page['title']))
        photos.append(dict(src='/guide-photos/'+name,alt=title+' — '+clean(page['title'][5:]),caption=title+' — '+clean(page['title'][5:]),author=author,license=license,license_url=meta.get('LicenseUrl',{}).get('value') or source+'#Licensing',source=source,modified='Redimensionamento da versão disponibilizada pelo Commons; enquadramento por CSS.'))
    if len(photos)<2:raise ValueError('Menos de duas fotos licenciadas: '+query)
    return photos
def main():
    p=ROOT/'guides.json';g=json.loads(p.read_text(encoding='utf-8'));DEST.mkdir(exist_ok=True)
    selected={k:v for k,v in g.items() if v.get('rome_day')}
    errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(fetch,v['photo_query'],v['title']):k for k,v in selected.items()}
        for f in concurrent.futures.as_completed(futures):
            k=futures[f]
            try:g[k]['photos']=f.result();print('OK',k,flush=True)
            except Exception as e:errors.append(k);print('FALHA',k,str(e),flush=True)
    # Dois exemplos para cada parte das visitas compostas.
    for k,query,label in [('vaticano-museus','intitle:"Sistine Chapel"','Capela Sistina'),('roma-popolo','intitle:"Santa Maria del Popolo"','Santa Maria del Popolo')]:
        try:
            extra=fetch(query,label);existing={p['source'] for p in g[k]['photos']};g[k]['photos'] += [p for p in extra if p['source'] not in existing]
        except Exception as e:errors.append(k);print('FALHA extra',k,str(e),flush=True)
    p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if errors:raise SystemExit('Falhas: '+', '.join(errors))
if __name__=='__main__':main()

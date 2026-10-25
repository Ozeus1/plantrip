"""Baixa fotografias livres e preserva autoria/licença; execute para atualizar o acervo."""
import concurrent.futures, hashlib, html, json, re, time, urllib.request, urllib.parse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'static'/'guide-photos'
HEADERS={'User-Agent':'Mozilla/5.0 Plantrip/1.0 (local educational travel guide; attribution preserved)'}

def request(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=35) as r:return r.read()
        except Exception:
            if attempt==2:raise
            time.sleep(1+attempt)

def clean(s):return html.unescape(re.sub('<[^>]+>','',s or '')).strip()

def fetch(title):
    dest=DEST/(hashlib.sha256(title.encode()).hexdigest()[:16]+'.jpg')
    metadata=dest.with_suffix('.json')
    if dest.exists() and metadata.exists():return title,json.loads(metadata.read_text(encoding='utf-8'))
    page=request('https://en.wikipedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_'),safe='')).decode()
    match=re.search(r'<meta property="og:image" content="([^"]+)"',page)
    image=html.unescape(match[1]) if match else ''
    if '/commons/' not in image or '.svg' in image.lower() or not re.search(r'\.(jpg|jpeg|webp|png)(?:[?/]|$)',image,re.I):
        fallback=re.search(r'src="((?:https:)?//(?:upload|thumb)\.wikimedia\.org/wikipedia/commons/[^"]+\.(?:jpg|jpeg)[^"]*)"',page,re.I)
        if not fallback:raise ValueError('Sem imagem livre no Commons: '+title)
        image=html.unescape(fallback[1])
        if image.startswith('//'):image='https:'+image
        image=re.sub(r'/\d+px-', '/1280px-',image)
    parts=urllib.parse.urlsplit(image).path.split('/commons/',1)[1].split('/')
    filename=urllib.parse.unquote(parts[3] if parts[0]=='thumb' else parts[2])
    source='https://commons.wikimedia.org/wiki/File:'+urllib.parse.quote(filename.replace(' ','_'),safe='')
    info=html.unescape(request(source).decode())
    author_match=re.search(r'<td[^>]+id="fileinfotpl_aut"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>',info,re.S)
    if not author_match:raise ValueError('Autoria não identificada: '+title)
    author=clean(author_match[1])
    licensing=info.split('<h2 id="Licensing">',1)[-1].split('<h2 id="filehistory">',1)[0]
    license_match=re.search(r'href="((?:https?:)?//creativecommons.org/(?:licenses|publicdomain)/[^"]+)"',licensing)
    if license_match:
        license_url=license_match[1]
        if license_url.startswith('//'):license_url='https:'+license_url
        code=urllib.parse.urlsplit(license_url).path.strip('/').split('/')
        license=('CC '+code[1].upper()+' '+code[2]) if code[0]=='licenses' else 'Domínio público / CC0'
    elif 'public domain' in licensing.lower():
        license='Domínio público';license_url=source+'#Licensing'
    else:raise ValueError('Licença livre não identificada: '+title)
    url=image.split('?',1)[0]
    blob=request(url)
    if not (blob.startswith(b'\xff\xd8') or blob.startswith(b'\x89PNG') or blob.startswith(b'RIFF')):raise ValueError('Formato inesperado: '+title)
    ext='.jpg' if blob.startswith(b'\xff\xd8') else '.png' if blob.startswith(b'\x89PNG') else '.webp'
    dest=dest.with_suffix(ext);dest.write_bytes(blob)
    result={'src':'/guide-photos/'+dest.name,'alt':title,'author':author,'license':license,'license_url':license_url,'source':source,'caption':title,'modified':'Redimensionamento para exibição; enquadramento via CSS. A fotografia mantém sua licença original.'}
    metadata.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return title,result

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    path=ROOT/'guides.json';guides=json.loads(path.read_text(encoding='utf-8'))
    titles=sorted({t for g in guides.values() for t in g['photo_titles']})
    photos={};errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        tasks={pool.submit(fetch,t):t for t in titles}
        for task in concurrent.futures.as_completed(tasks):
            title=tasks[task]
            try:
                key,value=task.result();photos[key]=value;print('OK',key,flush=True)
            except Exception as e:errors.append(title);print('FALHA',title,str(e),flush=True)
    for guide in guides.values():guide['photos']=[photos[t] for t in guide['photo_titles'] if t in photos]
    path.write_text(json.dumps(guides,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Fotos:',len(photos),'Falhas:',len(errors),flush=True)
    if errors:raise SystemExit(1)

if __name__=='__main__':main()

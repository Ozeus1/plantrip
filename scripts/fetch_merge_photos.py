"""Fotos do Commons para os guias novos (Sant'Ignazio e Londres a pé).

Passo 1: python scripts/fetch_merge_photos.py candidates  -> data/merge-photo-candidates.json (revisão editorial)
Passo 2: python scripts/fetch_merge_photos.py apply       -> baixa as escolhas de CHOICES para static/guide-photos
"""
import hashlib,json,sys,time,urllib.error,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fetch_rome_photos import request,clean
ROOT=Path(__file__).resolve().parents[1]
CAND=ROOT/'data'/'merge-photo-candidates.json'
QUERIES={'roma-santignazio':['intitle:"Sant\'Ignazio" Roma'],'londres-mall':['intitle:"Admiralty Arch"','intitle:"The Mall" London'],
 'londres-trafalgar':['intitle:"Trafalgar Square"'],'londres-horseguards':['intitle:"Horse Guards" London'],'londres-downing':['intitle:"Downing Street"'],
 'londres-westminsterbridge':['intitle:"Westminster Bridge"'],'londres-potters':['intitle:"Potters Fields"'],'londres-stkatharine':['intitle:"St Katharine Docks"'],
 'londres-southwark':['intitle:"Southwark Cathedral"'],'londres-borough':['intitle:"Borough Market"'],'londres-clink':['intitle:"Golden Hinde"','intitle:"Clink Street"'],
 'londres-globe':['intitle:"Shakespeare\'s Globe"'],'londres-onenewchange':['intitle:"One New Change"']}
def search(query):
 args=dict(action='query',generator='search',gsrsearch=query+' filetype:bitmap',gsrnamespace=6,gsrlimit=12,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=1000,format='json')
 for wait in (15,30,60,120,None):
  try:result=json.loads(request('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(args)));break
  except urllib.error.HTTPError as e:
   if e.code!=429 or wait is None:raise
   print('429, aguardando',wait,'s',flush=True);time.sleep(wait)
 time.sleep(3)
 return sorted(result.get('query',{}).get('pages',{}).values(),key=lambda x:x.get('index',999))
def candidates():
 out=json.loads(CAND.read_text(encoding='utf-8')) if CAND.exists() else {}
 for key,queries in QUERIES.items():
  if key in out:continue
  out[key]=[search(q) for q in queries]
  for n,pages in enumerate(out[key]):print(key,n,[(i,p['title'][5:60]) for i,p in enumerate(pages)],flush=True)
  CAND.write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
def norm(url):return urllib.parse.unquote(url).replace(' ','_')
def apply(choices):
 data=json.loads(CAND.read_text(encoding='utf-8'));p=ROOT/'guides.json';g=json.loads(p.read_text(encoding='utf-8'))
 for key,picks in choices.items():
  photos=[]
  for n,(q,index) in enumerate(picks):
   page=data[key][q][index];info=page['imageinfo'][0];meta=info['extmetadata'];source=info['descriptionurl']
   license=clean(meta.get('LicenseShortName',{}).get('value',''));author=clean(meta.get('Artist',{}).get('value',''))
   if not author or not('CC' in license or 'Public domain' in license or license=='PDM'):raise ValueError('Revisar licença: '+key)
   url=info.get('thumburl',info['url']);name=hashlib.sha256(info['url'].encode()).hexdigest()[:20]+Path(urllib.parse.urlsplit(url).path).suffix.lower();dest=ROOT/'static'/'guide-photos'/name
   if not dest.exists():
    blob=request(url)
    if not(blob.startswith(b'\xff\xd8') or blob.startswith(b'\x89PNG')):raise ValueError('Formato inesperado: '+key)
    dest.write_bytes(blob)
   label='vista geral' if n==0 else 'perspectiva e detalhe'
   photos.append(dict(src='/guide-photos/'+name,alt=g[key]['title']+' — '+label,caption=g[key]['title']+' — '+('vista geral' if n==0 else 'outro olhar'),author=author,license=license,license_url=(meta.get('LicenseUrl',{}).get('value') or source+'#Licensing').replace('http://','https://',1),source=source,modified='Fotografia do Commons em versão redimensionada; enquadramento por CSS.'))
  if len({x['source'] for x in photos})<2:raise ValueError('Fotos insuficientes: '+key)
  g[key]['photos']=photos;print('OK',key,flush=True)
 p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
 if sys.argv[1]=='candidates':candidates()
 else:apply(json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')))

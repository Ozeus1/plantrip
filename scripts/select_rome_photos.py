"""Seleção editorial por arquivo: evita homônimos, gravuras e recortes duplicados."""
import hashlib,json,sys,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fetch_rome_photos import request,clean
from fetch_guide_photos import fetch as wikipedia_photo
ROOT=Path(__file__).resolve().parents[1]
choices={'roma-campidoglio':[5,7],'roma-pantheon':[11,0],'roma-borghese':[8,9],'roma-adriano':[0,1],'roma-navona':[1,6],'roma-campo':[0,3],'roma-vittoriano':[2,4],'roma-forum':[2,7],'roma-spagna':[0,2],'roma-popolo':[0,2]}
p=ROOT/'guides.json';g=json.loads(p.read_text(encoding='utf-8'))
data=json.loads((ROOT/'data'/'rome-photo-candidates.json').read_text(encoding='utf-8'))
for key,indices in choices.items():
 selected=[]
 for n,index in enumerate(indices):
  info=data[key][index]['imageinfo'][0];meta=info['extmetadata'];license=clean(meta.get('LicenseShortName',{}).get('value',''));author=clean(meta.get('Artist',{}).get('value',''))
  if not author or not ('CC' in license or 'Public domain' in license or license=='PDM'):raise ValueError('Revisar licença: '+key)
  url=info.get('thumburl',info['url']);name=hashlib.sha256(info['url'].encode()).hexdigest()[:20]+Path(urllib.parse.urlsplit(url).path).suffix.lower();dest=ROOT/'static'/'guide-photos'/name
  if not dest.exists():dest.write_bytes(request(url))
  source=info['descriptionurl'];license_url=meta.get('LicenseUrl',{}).get('value') or source+'#Licensing'
  license_url=license_url.replace('http://','https://',1)
  selected.append(dict(src='/guide-photos/'+name,alt=g[key]['title']+' — fotografia '+str(n+1),caption=g[key]['title']+' — '+('vista do local' if n==0 else 'outro olhar'),author=author,license=license,license_url=license_url,source=source,modified='Versão redimensionada do Commons para exibição; enquadramento por CSS.'))
 if key=='roma-popolo':selected += g[key]['photos'][2:]
 g[key]['photos']=selected
 print('Selecionadas',key,flush=True)
for key,article,keep in [('roma-galleria','Galleria Borghese',-1),('roma-castel',"Castel Sant'Angelo",0),('roma-sanluigi','San Luigi dei Francesi',1),('roma-borghese','Villa Borghese gardens',1),('roma-palatino','Palatine Hill',1),('vaticano-saopedro',"St. Peter's Basilica",0)]:
 try:
  _,photo=wikipedia_photo(article);old=g[key]['photos'][keep]
  if photo['source']!=old['source']:g[key]['photos']=[photo,old]
  print('Vista geral',key,flush=True)
 except Exception as e:print('Mantidas fotografias selecionadas:',key,e,flush=True)
try:
 _,photo=wikipedia_photo('Santa Maria del Popolo');g['roma-popolo']['photos']=g['roma-popolo']['photos'][:2]+[photo,g['roma-popolo']['photos'][-1]]
except Exception as e:print('Santa Maria:',e,flush=True)
for guide in g.values():
 for photo in guide['photos']:
  photo['license_url']=photo['license_url'].replace('http://','https://',1)
  if guide.get('rome_day') and ' — ' in photo['caption']:photo['caption']=photo['caption'].split(' — ')[0]+' — '+('outro olhar' if guide['photos'].index(photo)%2 else 'vista do local')
p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

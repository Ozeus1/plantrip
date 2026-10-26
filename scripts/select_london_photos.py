"""Escolhas editoriais: monumentos corretos, duas fotos distintas e créditos completos."""
import hashlib,json,sys,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fetch_rome_photos import request,clean
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'guides.json';g=json.loads(p.read_text(encoding='utf-8'));data=json.loads((ROOT/'data'/'london-photo-candidates.json').read_text(encoding='utf-8'))
choices={'londres-buckingham':[3,4],'londres-stjames':[0,1],'londres-westminster':[0,1],'londres-cabines':[4,2],'londres-bigben':[1,0],'londres-parlamento':[0,1],'londres-southbank':[1,0],'londres-tower':[0,1],'londres-towerbridge':[0,8],'londres-londonbridge':[2,1],'londres-tate':[0,2],'londres-millennium':[2,0],'londres-city':[9,5]}
def norm(url):return urllib.parse.unquote(url).replace(' ','_')
for key,indices in choices.items():
 photos=[] if key=='londres-cabines' else g[key]['photos'][:1]
 for index in indices:
  if len(photos)>=2:break
  info=data[key][index]['imageinfo'][0];meta=info['extmetadata'];source=info['descriptionurl']
  if norm(source) in {norm(x['source']) for x in photos}:continue
  license=clean(meta.get('LicenseShortName',{}).get('value',''));author=clean(meta.get('Artist',{}).get('value',''))
  if not author or not ('CC' in license or 'Public domain' in license or license=='PDM'):raise ValueError('Revisar licença: '+key)
  url=info.get('thumburl',info['url']);name=hashlib.sha256(info['url'].encode()).hexdigest()[:20]+Path(urllib.parse.urlsplit(url).path).suffix.lower();dest=ROOT/'static'/'guide-photos'/name
  if not dest.exists():
   blob=request(url)
   if not(blob.startswith(b'\xff\xd8') or blob.startswith(b'\x89PNG')):raise ValueError('Formato inesperado')
   dest.write_bytes(blob)
  photos.append(dict(src='/guide-photos/'+name,alt=g[key]['title'],caption=g[key]['title']+' — outro olhar',author=author,license=license,license_url=(meta.get('LicenseUrl',{}).get('value') or source+'#Licensing').replace('http://','https://',1),source=source,modified='Fotografia do Commons em versão redimensionada; enquadramento por CSS.'))
 if len(photos)<2:raise ValueError('Fotos insuficientes: '+key)
 for n,photo in enumerate(photos):
  photo['alt']=g[key]['title']+' — '+('vista geral' if n==0 else 'perspectiva e detalhe')
  photo['caption']=g[key]['title']+' — '+('vista geral' if n==0 else 'outro olhar')
  photo['license_url']=photo['license_url'].replace('http://','https://',1)
 if key=='londres-city':photos[1]['caption']='Interior de St Paul’s — referência para a alternativa de visita antecipada'
 g[key]['photos']=photos
 print('OK',key,flush=True)
p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

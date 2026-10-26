"""Seleção editorial de duas fotos por guia; crédito, licença e origem preservados."""
import hashlib,json,sys,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fetch_rome_photos import request,clean
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'guides.json';g=json.loads(p.read_text(encoding='utf-8'));data=json.loads((ROOT/'data'/'paris-photo-candidates.json').read_text(encoding='utf-8'))
choices={'paris-eiffel':[0,7],'paris-sena':[0,7],'paris-louvre':[3,5],'paris-tuileries':[2,4],'paris-cite':[4,2],'paris-luxemburgo':[0,2],'paris-versalhes':[0,3],'paris-montmartre':[0,2],'paris-opera':[7,0],'paris-arco':[4,6],'paris-marais':[1,0],'champagne-reims':[0,3],'paris-champmars':[0,2],'paris-iena':[0,1],'paris-trocadero':[1,2],'paris-sacre':[1,0],'paris-moulin':[0,3],'paris-deuxmoulins':[0,4],'paris-concorde':[0,3],'paris-champs':[0,4],'paris-reims':[2,7],'champagne-ruinart':[2,4],'paris-parly2':[3,1],'paris-saintecroix':[1,6],'paris-pompidou':[2],'paris-pantheon':[0,3],'paris-garenord':[1,4],'paris-outlet':[0,1]}
replace={'champagne-reims','champagne-ruinart','paris-trocadero','paris-moulin','paris-saintecroix','paris-outlet'}
def norm(x):return urllib.parse.unquote(x).replace(' ','_')
errors=[]
for key,indices in choices.items():
 photos=[] if key in replace else g[key]['photos'][:1]
 try:
  for index in indices:
   if len(photos)>=2:break
   info=data[key][index]['imageinfo'][0];meta=info['extmetadata'];source=info['descriptionurl']
   if norm(source) in {norm(p['source']) for p in photos}:continue
   license=clean(meta.get('LicenseShortName',{}).get('value',''));author=clean(meta.get('Artist',{}).get('value',''))
   if not author or not ('CC' in license or 'Public domain' in license or license=='PDM'):raise ValueError('Revisar licença: '+key)
   url=info.get('thumburl',info['url']);name=hashlib.sha256(info['url'].encode()).hexdigest()[:20]+Path(urllib.parse.urlsplit(url).path).suffix.lower();dest=ROOT/'static'/'guide-photos'/name
   if not dest.exists():
    blob=request(url)
    if not(blob.startswith(b'\xff\xd8') or blob.startswith(b'\x89PNG')):raise ValueError('Formato inesperado')
    dest.write_bytes(blob)
   photos.append(dict(src='/guide-photos/'+name,author=author,license=license,license_url=(meta.get('LicenseUrl',{}).get('value') or source+'#Licensing').replace('http://','https://',1),source=source,modified='Versão disponibilizada pelo Commons redimensionada para exibição; enquadramento por CSS.'))
  if len(photos)<2:raise ValueError('Fotos insuficientes: '+key)
  for n,photo in enumerate(photos):
   label='Rua Sainte-Croix de la Bretonnerie — entorno do restaurante' if key=='paris-saintecroix' else g[key]['title']
   photo['alt']=label+' — '+('vista geral' if n==0 else 'perspectiva e detalhe');photo['caption']=label+' — '+('vista do local' if n==0 else 'outro olhar');photo['license_url']=photo['license_url'].replace('http://','https://',1)
  if key=='paris-pompidou':
   for photo in photos:photo['caption']+=' (referência anterior às obras)'
  g[key]['photos']=photos
  print('OK',key,flush=True)
 except Exception as e:errors.append(key);print('FALHA',key,e,flush=True)
# Ajustes finais que não devem ser perdidos ao salvar a pesquisa de imagens.
g['paris-saintecroix']['booking']=g['paris-saintecroix']['booking'].replace('contato@/canal oficial contact@jaja-resto.com','e-mail contact@jaja-resto.com')
g['paris-reims']['tips'].append('Se a estrada atrasar, dispensar a parada da catedral e seguir à primeira maison; não comprometer o horário reservado.')
p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if errors:raise SystemExit('Falhas: '+', '.join(errors))

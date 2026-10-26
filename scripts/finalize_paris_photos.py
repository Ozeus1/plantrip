"""Ajustes de curadoria após a conferência visual do acervo."""
import hashlib,json,sys,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fetch_rome_photos import request,clean
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'guides.json';g=json.loads(p.read_text(encoding='utf-8'))
def photo(page,label):
 info=page['imageinfo'][0];meta=info['extmetadata'];license=clean(meta.get('LicenseShortName',{}).get('value',''));author=clean(meta.get('Artist',{}).get('value',''))
 if not author or not ('CC' in license or 'Public domain' in license or license=='PDM'):raise ValueError('Licença incompleta')
 url=info.get('thumburl',info['url']);name=hashlib.sha256(info['url'].encode()).hexdigest()[:20]+Path(urllib.parse.urlsplit(url).path).suffix.lower();dest=ROOT/'static'/'guide-photos'/name
 if not dest.exists():dest.write_bytes(request(url))
 source=info['descriptionurl']
 return dict(src='/guide-photos/'+name,alt=label,caption=label,author=author,license=license,license_url=(meta.get('LicenseUrl',{}).get('value') or source+'#Licensing').replace('http://','https://',1),source=source,modified='Versão redimensionada do Commons; enquadramento por CSS.')
data=json.loads((ROOT/'data'/'paris-photo-candidates.json').read_text(encoding='utf-8'))
ruinart=json.loads((ROOT/'data'/'ruinart-photo-review.json').read_text(encoding='utf-8'))
g['champagne-ruinart']['photos'][0]=photo(ruinart[6],'Jardins da Maison Ruinart — visita conforme modalidade reservada')
g['champagne-ruinart']['photos'][1]['caption']='Registro histórico das caves Ruinart — imagem de referência'
g['paris-arco']['photos'][1]=photo(data['paris-arco'][6],'Arco do Triunfo de l’Étoile — outra perspectiva')
g['paris-tuileries']['photos'][1]=photo(data['paris-tuileries'][4],'Jardim das Tuileries — alamedas e paisagem')
g['paris-pompidou']['photos']=list(reversed(g['paris-pompidou']['photos']))
p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Curadoria final concluída.')

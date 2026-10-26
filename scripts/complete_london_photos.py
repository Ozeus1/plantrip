import hashlib,json,sys,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fetch_rome_photos import request,clean
from fetch_guide_photos import fetch
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'guides.json';g=json.loads(p.read_text(encoding='utf-8'))
candidates=json.loads((ROOT/'data'/'london-photo-candidates.json').read_text(encoding='utf-8'))
for key,query in [('londres-stjames','intitle:"St James" intitle:"Park" London lake'),('londres-city','intitle:"St Paul" intitle:"Cathedral" London')]:
 if key not in candidates:
  args=dict(action='query',generator='search',gsrsearch=query+' filetype:bitmap',gsrnamespace=6,gsrlimit=10,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=1000,format='json')
  result=json.loads(request('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(args)))
  candidates[key]=sorted(result.get('query',{}).get('pages',{}).values(),key=lambda x:x.get('index',999))
  print(key,[(i,x['title']) for i,x in enumerate(candidates[key])],flush=True)
(ROOT/'data'/'london-photo-candidates.json').write_text(json.dumps(candidates,ensure_ascii=False),encoding='utf-8')
try:
 _,photo=fetch("St James's Park");g['londres-stjames']['photos']=[photo]
except Exception as e:print('Parque:',e,flush=True)
p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

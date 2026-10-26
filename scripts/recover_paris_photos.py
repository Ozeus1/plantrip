import json,sys,time,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fetch_rome_photos import request
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'data'/'paris-photo-candidates.json';data=json.loads(p.read_text(encoding='utf-8'))
queries={'paris-deuxmoulins':'intitle:"Café des 2 Moulins"','paris-concorde':'intitle:"Place de la Concorde" fountain','paris-champs':'intitle:"Champs-Élysées" Paris','paris-reims':'intitle:"Reims Cathedral"','paris-moulin':'intitle:"Moulin Rouge" Paris -btv1b -painting'}
for key,query in queries.items():
 args=dict(action='query',generator='search',gsrsearch=query+' filetype:bitmap',gsrnamespace=6,gsrlimit=8,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=1000,format='json')
 try:
  result=json.loads(request('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(args)))
  data[key]=sorted(result.get('query',{}).get('pages',{}).values(),key=lambda x:x.get('index',999));print(key,[(i,x['title']) for i,x in enumerate(data[key])],flush=True)
 except Exception as e:print('FALHA',key,e,flush=True)
 time.sleep(2)
p.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')

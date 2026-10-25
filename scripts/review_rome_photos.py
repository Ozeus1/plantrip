import json,sys,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fetch_rome_photos import request
ROOT=Path(__file__).resolve().parents[1]
QUERIES={
 'roma-campidoglio':'intitle:"Piazza Venezia" intitle:"Rome"',
 'roma-pantheon':'intitle:"Pantheon" intitle:"Rome" exterior',
 'roma-borghese':'intitle:"Villa Borghese" garden Rome -squirrel -MET -painting -portrait',
 'roma-adriano':'intitle:"Temple of Hadrian" intitle:"Rome"',
 'roma-navona':'intitle:"Piazza Navona" fountain',
 'roma-campo':'intitle:"Campo" intitle:"Fiori" Rome',
 'roma-vittoriano':'intitle:"Vittoriano" front',
 'roma-forum':'intitle:"Roman Forum" intitle:"Rome"',
 'roma-spagna':'intitle:"Piazza di Spagna" intitle:"Rome" -object -drawing',
 'roma-popolo':'intitle:"Piazza del Popolo" intitle:"Rome"',
 'roma-galleria':'intitle:"Galleria Borghese" sculpture -ceiling'
}
results={}
for key,query in QUERIES.items():
 args=dict(action='query',generator='search',gsrsearch=query+' filetype:bitmap',gsrnamespace=6,gsrlimit=12,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=1000,format='json')
 try:
  data=json.loads(request('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(args)))
  pages=sorted(data.get('query',{}).get('pages',{}).values(),key=lambda x:x.get('index',999))
  results[key]=pages
  print(key,[(i,p['title']) for i,p in enumerate(pages)],flush=True)
 except Exception as e:print('FALHA',key,e,flush=True)
(ROOT/'data'/'rome-photo-candidates.json').write_text(json.dumps(results,ensure_ascii=False),encoding='utf-8')

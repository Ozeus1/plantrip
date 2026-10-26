"""Pesquisa de fotografias livres para os guias de Paris e Champagne."""
import json,sys,time,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fetch_guide_photos import fetch
from fetch_rome_photos import request
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=ROOT/'guides.json';g=json.loads(p.read_text(encoding='utf-8'));candidates={}
 chosen={k:v for k,v in g.items() if v.get('paris_day') or k in ('paris-garenord','paris-outlet')}
 for k,v in chosen.items():
  try:
   _,photo=fetch(v['photo_article'].replace('’',"'"));g[k]['photos']=[photo]
  except Exception as e:print('FOTO PRINCIPAL',k,str(e),flush=True)
  try:
   args=dict(action='query',generator='search',gsrsearch=v['photo_query']+' filetype:bitmap',gsrnamespace=6,gsrlimit=8,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=1000,format='json')
   result=json.loads(request('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(args)))
   pages=sorted(result.get('query',{}).get('pages',{}).values(),key=lambda x:x.get('index',999));candidates[k]=pages
   print(k,[(i,x['title']) for i,x in enumerate(pages)],flush=True)
  except Exception as e:print('FALHA CANDIDATOS',k,e,flush=True)
  time.sleep(1)
 (ROOT/'data'/'paris-photo-candidates.json').write_text(json.dumps(candidates,ensure_ascii=False),encoding='utf-8')
 p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()

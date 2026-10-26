"""Acervo de Londres: foto principal e candidatos do Commons para revisão editorial."""
import json,sys,time,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fetch_guide_photos import fetch
from fetch_rome_photos import request
ROOT=Path(__file__).resolve().parents[1]
QUERIES={
 'londres-buckingham':'intitle:"Buckingham Palace" London facade',
 'londres-stjames':'intitle:"St James" intitle:"Park" London lake',
 'londres-westminster':'intitle:"Westminster Abbey" London facade',
 'londres-cabines':'intitle:"telephone" intitle:"Westminster"',
 'londres-bigben':'intitle:"Elizabeth Tower" London',
 'londres-parlamento':'intitle:"Palace of Westminster" London river',
 'londres-southbank':'intitle:"London Eye" London',
 'londres-tower':'intitle:"Tower of London" White Tower',
 'londres-towerbridge':'intitle:"Tower Bridge" London',
 'londres-londonbridge':'intitle:"London Bridge" -Tower -Arizona -Havasu -Rennie -old -Old',
 'londres-tate':'intitle:"Tate Modern" Bankside',
 'londres-millennium':'intitle:"Millennium Bridge" London',
 'londres-city':'intitle:"St Paul" Cathedral London exterior'}
def main():
 p=ROOT/'guides.json';g=json.loads(p.read_text(encoding='utf-8'));candidates={}
 for k,query in QUERIES.items():
  try:
   if k!='londres-cabines':
    _,photo=fetch(g[k]['photo_article']);g[k]['photos']=[photo]
   args=dict(action='query',generator='search',gsrsearch=query+' filetype:bitmap',gsrnamespace=6,gsrlimit=10,prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=1000,format='json')
   result=json.loads(request('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(args)))
   pages=sorted(result.get('query',{}).get('pages',{}).values(),key=lambda x:x.get('index',999));candidates[k]=pages
   print(k,[(i,v['title']) for i,v in enumerate(pages)],flush=True)
  except Exception as e:print('FALHA',k,e,flush=True)
  time.sleep(1)
 (ROOT/'data'/'london-photo-candidates.json').write_text(json.dumps(candidates,ensure_ascii=False),encoding='utf-8')
 p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()

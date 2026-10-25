"""Auditoria opcional de links oficiais, sem dependências externas."""
import concurrent.futures,json,urllib.request,urllib.error
from pathlib import Path

def check(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 Plantrip/1.0'}),timeout=25) as r:return url,r.status
    except urllib.error.HTTPError as e:return url,e.code
    except Exception:return url,'indisponível'

if __name__=='__main__':
    guides=json.loads((Path(__file__).resolve().parents[1]/'guides.json').read_text(encoding='utf-8'))
    urls=sorted({s['url'] for g in guides.values() for s in g['sources']})
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for url,status in pool.map(check,urls):print(status,url,flush=True)

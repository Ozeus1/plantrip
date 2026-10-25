"""Catálogo editorial e vínculo estável entre passeios e seus guias."""
import json
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=2)
def _catalog(version):
    return json.loads((Path(__file__).parent/'guides.json').read_text(encoding='utf-8'))

def catalog():
    return _catalog((Path(__file__).parent/'guides.json').stat().st_mtime_ns)

def attach_guides(c):
    for key,g in catalog().items():
        c.execute("UPDATE entries SET guide_key=? WHERE kind='tour' AND title=? AND place=? AND (guide_key IS NULL OR guide_key='')",(key,g['title'],g['city']))

def guide_for(entry):
    return catalog().get(entry['guide_key']) if entry['guide_key'] else None

def preview(entry):
    g=guide_for(entry)
    return {'key':g['key'],'intro':g['intro'],'photos':g['photos'],'history':g['history']} if g else None

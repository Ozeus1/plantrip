"""Versões leves das fotos para exibição (miniatura, celular e desktop).

O arquivo original continua intacto (até 100 MB); as versões reduzidas são geradas uma
única vez, guardadas em uploads/variants e servidas no lugar do original quando a página
pede /media/<id>?w=<largura>. Sem Pillow, ou com formato não suportado, vale o original.
"""
import threading
from pathlib import Path

WIDTHS = (480, 1280, 1920)
WARM = (480, 1280)
RESIZABLE = {'image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif'}
_locks = {}
_guard = threading.Lock()

try:
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = 200_000_000
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass
except ImportError:  # pragma: no cover - o app continua servindo os originais
    Image = None


def variant_path(source: Path, width: int) -> Path:
    return source.parent / 'variants' / f'{source.stem}-{width}.webp'


def _lock(key):
    with _guard:
        return _locks.setdefault(key, threading.Lock())


def variant(source: Path, mime: str, width: int):
    """Caminho da versão reduzida, criando-a se preciso; None quando deve valer o original."""
    if Image is None or width not in WIDTHS or mime not in RESIZABLE or not source.is_file():
        return None
    target = variant_path(source, width)
    if target.is_file():
        return target
    with _lock(str(target)):
        if target.is_file():
            return target
        try:
            with Image.open(source) as img:
                img.draft('RGB', (width, width))  # JPEG: decodifica já reduzido, bem mais rápido
                img = ImageOps.exif_transpose(img)  # fotos de celular na orientação certa
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA' if 'A' in img.getbands() else 'RGB')
                img.thumbnail((width, width), Image.LANCZOS)
                target.parent.mkdir(exist_ok=True)
                temp = target.with_suffix('.tmp')
                img.save(temp, 'WEBP', quality=80 if width > 480 else 72, method=4)
                temp.replace(target)
            return target
        except Exception:
            return None


def warm(source: Path, mime: str):
    """Prepara em segundo plano as versões mais usadas logo após o envio."""
    if Image is None or mime not in RESIZABLE:
        return
    def run():
        for width in WARM:
            variant(source, mime, width)
    threading.Thread(target=run, daemon=True).start()


def drop(source: Path):
    for width in WIDTHS:
        variant_path(source, width).unlink(missing_ok=True)


def backfill(sources):
    """Fotos já enviadas antes desta versão: gera as variantes em segundo plano, uma por vez."""
    if Image is None:
        return
    items = [(Path(path), mime) for path, mime in sources if mime in RESIZABLE]
    def run():
        for source, mime in items:
            for width in WARM:
                if not variant_path(source, width).is_file():
                    variant(source, mime, width)
    threading.Thread(target=run, daemon=True, name='media-backfill').start()

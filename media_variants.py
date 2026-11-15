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
    from PIL import Image, ImageOps, ImageEnhance
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


def edit(source: Path, target_stem: Path, ops: dict):
    """Aplica giro, espelho, corte e ajustes de cor ao arquivo; devolve (caminho novo, mime).

    ops: rotate (0/90/180/270, horário), flip_h, flip_v, crop {x,y,w,h} em frações da imagem já
    girada, brightness/contrast/saturation (0.5 a 1.5; 1 = sem mudança). Levanta ValueError.
    """
    if Image is None:
        raise ValueError('Editor indisponível neste servidor')
    def factor(key):
        value = ops.get(key, 1)
        if type(value) not in (int, float) or not 0.5 <= value <= 1.5:
            raise ValueError('Ajuste inválido: ' + key)
        return float(value)
    rotate = ops.get('rotate', 0)
    if type(rotate) is not int or rotate not in (0, 90, 180, 270):
        raise ValueError('Giro inválido')
    bright, contrast, color = factor('brightness'), factor('contrast'), factor('saturation')
    crop = ops.get('crop')
    if crop is not None:
        if not isinstance(crop, dict) or any(type(crop.get(k)) not in (int, float) for k in 'xywh'):
            raise ValueError('Corte inválido')
        x, y, w, h = (float(crop[k]) for k in 'xywh')
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1.0001 or y + h > 1.0001:
            raise ValueError('Corte fora da imagem')
    try:
        with Image.open(source) as img:
            fmt = img.format
            exif = img.getexif()
            img = ImageOps.exif_transpose(img)
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA' if 'A' in img.getbands() or 'transparency' in img.info else 'RGB')
            if rotate:
                img = img.transpose({90: Image.ROTATE_270, 180: Image.ROTATE_180, 270: Image.ROTATE_90}[rotate])
            if ops.get('flip_h'):
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            if ops.get('flip_v'):
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            if crop is not None:
                W, H = img.size
                box = (round(x * W), round(y * H), min(W, round((x + w) * W)), min(H, round((y + h) * H)))
                if box[2] - box[0] < 16 or box[3] - box[1] < 16:
                    raise ValueError('Corte pequeno demais')
                img = img.crop(box)
            if (bright, contrast, color) != (1, 1, 1):
                alpha = img.getchannel('A') if img.mode == 'RGBA' else None
                rgb = img.convert('RGB')
                # Mesma conta dos filtros do navegador (brilho, depois contraste em torno do cinza médio).
                lut = [max(0, min(255, round((v * bright - 127.5) * contrast + 127.5))) for v in range(256)]
                rgb = rgb.point(lut * 3)
                if color != 1:
                    rgb = ImageEnhance.Color(rgb).enhance(color)
                if alpha:
                    rgb.putalpha(alpha)
                img = rgb
            exif.pop(0x0112, None)  # orientação já aplicada
            try:
                meta = exif.tobytes()
            except Exception:
                meta = b''
            if fmt == 'PNG':
                target, mime = target_stem.with_suffix('.png'), 'image/png'
                img.save(target, 'PNG', optimize=True)
            elif fmt == 'WEBP':
                target, mime = target_stem.with_suffix('.webp'), 'image/webp'
                img.save(target, 'WEBP', quality=92, method=4)
            else:
                target, mime = target_stem.with_suffix('.jpg'), 'image/jpeg'
                img.convert('RGB').save(target, 'JPEG', quality=93, subsampling=0, optimize=True, exif=meta)
            return target, mime
    except ValueError:
        raise
    except Exception:
        raise ValueError('Não foi possível editar esta imagem')

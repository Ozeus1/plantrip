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
    from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageChops
    Image.MAX_IMAGE_PIXELS = 200_000_000
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass
except ImportError:  # pragma: no cover - o app continua servindo os originais
    Image = None

try:  # apagar objetos (retoque) é opcional: sem OpenCV o resto do editor continua funcionando
    import cv2
    import numpy
except ImportError:  # pragma: no cover
    cv2 = None


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


def remove(path: Path):
    """Apaga o arquivo; no Windows ele pode estar aberto por instantes (miniaturas sendo geradas), então insiste."""
    import time
    for attempt in range(40):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            time.sleep(.05)
    path.unlink(missing_ok=True)


def drop(source: Path):
    for width in WIDTHS:
        remove(variant_path(source, width))


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


def readable(raw: bytes) -> bool:
    """O conteúdo enviado abre como imagem? (sem Pillow, aceita.)"""
    if Image is None:
        return True
    import io
    try:
        with Image.open(io.BytesIO(raw)) as img:
            img.verify()
        return True
    except Exception:
        return False


def focus_mask(size, x, y, r):
    """Máscara do objeto em foco: 255 no centro, caindo suavemente até 0 na borda do círculo.

    x, y em frações da imagem; r em fração do menor lado. Mesma conta da prévia no navegador.
    """
    W, H = size
    k = 256 / max(W, H)
    w, h = max(1, round(W * k)), max(1, round(H * k))
    radius = r * min(W, H)
    data = bytearray(w * h)
    for j in range(h):
        dy = ((j + .5) / h - y) * H
        for i in range(w):
            dx = ((i + .5) / w - x) * W
            t = min(1, max(0, ((dx * dx + dy * dy) ** .5 / radius - .6) / .4))
            data[j * w + i] = round(255 * (1 - t * t * (3 - 2 * t)))
    return Image.frombytes('L', (w, h), bytes(data)).resize(size, Image.BILINEAR)


def apply_focus(img, focus):
    """Realça a nitidez (na foto toda ou só no objeto marcado) e, se pedido, suaviza o fundo."""
    sharpen, blur, marked = focus['sharpen'], focus['blur'], focus['x'] is not None
    rgb = img.convert('RGB')
    side = max(rgb.size)
    result = rgb
    if sharpen:
        result = rgb.filter(ImageFilter.UnsharpMask(radius=max(1.2, side / 700), percent=round(sharpen * 220), threshold=2))
    if marked:
        back = rgb.filter(ImageFilter.GaussianBlur(blur * side / 130)) if blur else rgb
        result = Image.composite(result, back, focus_mask(rgb.size, focus['x'], focus['y'], focus['r']))
    if img.mode == 'RGBA':
        result.putalpha(img.getchannel('A'))
    return result


def apply_look(img, look):
    """Acabamento dos filtros prontos: pele suave, temperatura, desbotado e vinheta (nessa ordem)."""
    alpha = img.getchannel('A') if img.mode == 'RGBA' else None
    rgb = img.convert('RGB')
    W, H = rgb.size
    soften, warmth, fade, vignette = look['soften'], look['warmth'], look['fade'], look['vignette']
    if soften:
        # Suaviza só onde a textura é fina (pele); contornos fortes como olhos e cabelo ficam nítidos.
        blurred = rgb.filter(ImageFilter.GaussianBlur(max(1.5, max(W, H) / 250)))
        mask = ImageChops.difference(rgb, blurred).convert('L').point([round(255 * soften * max(0, 1 - d / 40)) for d in range(256)])
        rgb = Image.composite(blurred, rgb, mask)
    if warmth or fade:
        def lut(gain):
            return [max(0, min(255, round(40 * fade + min(255, v * gain) * (1 - .25 * fade)))) for v in range(256)]
        rgb = rgb.point(lut(1 + .18 * warmth) + lut(1) + lut(1 - .18 * warmth))
    if vignette:
        k = 256 / max(W, H)
        w, h = max(1, round(W * k)), max(1, round(H * k))
        data = bytearray(w * h)
        for j in range(h):
            dy = ((j + .5) / h - .5) * 2
            for i in range(w):
                dx = ((i + .5) / w - .5) * 2
                t = min(1, max(0, ((dx * dx + dy * dy) ** .5 / 1.41421356 - .35) / .65))
                data[j * w + i] = round(255 * (1 - .75 * vignette * t * t * (3 - 2 * t)))
        shade = Image.frombytes('L', (w, h), bytes(data)).resize((W, H), Image.BILINEAR)
        rgb = ImageChops.multiply(rgb, Image.merge('RGB', (shade, shade, shade)))
    if alpha:
        rgb.putalpha(alpha)
    return rgb


def clean_erase(strokes):
    """Valida os traços do pincel: lista de {r, pts:[[x,y],...]} em frações da imagem original."""
    if strokes is None:
        return None
    if not isinstance(strokes, list) or len(strokes) > 80:
        raise ValueError('Marcação para apagar inválida')
    clean = []
    for stroke in strokes:
        r, pts = (stroke.get('r'), stroke.get('pts')) if isinstance(stroke, dict) else (None, None)
        if type(r) not in (int, float) or not .002 <= r <= .15 or not isinstance(pts, list) or not 1 <= len(pts) <= 600:
            raise ValueError('Marcação para apagar inválida')
        for p in pts:
            if not isinstance(p, list) or len(p) != 2 or any(type(v) not in (int, float) or not 0 <= v <= 1 for v in p):
                raise ValueError('Marcação para apagar inválida')
        clean.append((float(r), [(float(x), float(y)) for x, y in pts]))
    return clean or None


def erase_mask(size, strokes):
    """Máscara (255 = apagar) com os traços do pincel; o raio é fração do menor lado."""
    from PIL import ImageDraw
    W, H = size
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    for r, pts in strokes:
        radius = max(2, r * min(W, H))
        xy = [(x * W, y * H) for x, y in pts]
        if len(xy) > 1:
            draw.line(xy, fill=255, width=round(radius * 2), joint='curve')
        for x, y in xy:
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)
    return mask


def apply_erase(img, strokes):
    """Apaga o que foi pintado, preenchendo a área com a continuação do entorno (retoque Telea)."""
    if cv2 is None:
        raise ValueError('Apagar objetos não está disponível neste servidor')
    mask = erase_mask(img.size, strokes)
    box = mask.getbbox()
    if not box:
        return img
    W, H = img.size
    if (box[2] - box[0]) * (box[3] - box[1]) > .35 * W * H:
        raise ValueError('Área grande demais para apagar: pinte só o objeto')
    margin = max(24, round(.04 * max(W, H)))
    box = (max(0, box[0] - margin), max(0, box[1] - margin), min(W, box[2] + margin), min(H, box[3] + margin))
    region, hole = img.crop(box).convert('RGB'), mask.crop(box)
    # Trabalha num recorte reduzido (rápido mesmo em fotos enormes) e devolve só a área pintada.
    scale = min(1, 1400 / max(region.size))
    small = tuple(max(1, round(v * scale)) for v in region.size)
    work = region.resize(small, Image.LANCZOS) if scale < 1 else region
    wide = hole.resize(small, Image.BILINEAR).point(lambda v: 255 if v > 16 else 0).filter(ImageFilter.MaxFilter(5))
    filled = cv2.inpaint(numpy.asarray(work), numpy.asarray(wide), max(3, round(6 * scale + 2)), cv2.INPAINT_TELEA)
    filled = Image.fromarray(filled).resize(region.size, Image.BICUBIC) if scale < 1 else Image.fromarray(filled)
    soft = wide.resize(region.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(max(1.5, 1.5 / scale)))
    # O preenchimento sai liso; devolve a ele o grão da foto (medido fora da área) para não ficar uma mancha lavada.
    pixels = numpy.asarray(region, dtype=numpy.float32)
    grain = pixels - numpy.asarray(region.filter(ImageFilter.GaussianBlur(2)), dtype=numpy.float32)
    outside = numpy.asarray(soft) == 0
    if outside.sum() > 500:
        level = min(12.0, float(numpy.median(numpy.abs(grain[outside]))) * 1.4826)
        if level > .4:
            noise = numpy.random.default_rng(0).normal(0, level, pixels.shape[:2] + (1,))
            filled = Image.fromarray(numpy.clip(numpy.asarray(filled, dtype=numpy.float32) + noise, 0, 255).astype(numpy.uint8))
    patch = Image.composite(filled, region, soft)
    result = img.copy()
    if img.mode == 'RGBA':
        patch.putalpha(img.crop(box).getchannel('A'))
    result.paste(patch, box[:2])
    return result


def erase_preview(source: Path, strokes, width=1280):
    """JPEG da foto (orientação original, reduzida) já com os objetos apagados, para a prévia do editor."""
    import io
    strokes = clean_erase(strokes)
    if Image is None or not strokes:
        raise ValueError('Pinte o objeto a apagar')
    try:
        with Image.open(source) as img:
            img.draft('RGB', (width, width))
            img = ImageOps.exif_transpose(img).convert('RGB')
            img.thumbnail((width, width), Image.LANCZOS)
            out = io.BytesIO()
            apply_erase(img, strokes).save(out, 'JPEG', quality=88)
            return out.getvalue()
    except ValueError:
        raise
    except Exception:
        raise ValueError('Não foi possível apagar nesta imagem')


def edit(source: Path, target_stem: Path, ops: dict):
    """Aplica giro, espelho, corte e ajustes de cor ao arquivo; devolve (caminho novo, mime).

    ops: rotate (0/90/180/270, horário), flip_h, flip_v, crop {x,y,w,h} em frações da imagem já
    girada, erase (traços do pincel sobre a imagem original, apagados antes de tudo), brightness/contrast (0.5 a 1.5) e saturation (0 a 2; 1 = sem mudança), look {warmth -1..1,
    vignette, fade, soften 0..1} aplicado depois do corte e antes de brilho/contraste/cor, focus {x,y,r,sharpen,blur}
    (x/y nulos = nitidez na foto toda; posição em frações da imagem girada, antes do corte). Levanta ValueError.
    """
    if Image is None:
        raise ValueError('Editor indisponível neste servidor')
    def factor(key, low=0.5, high=1.5):
        value = ops.get(key, 1)
        if type(value) not in (int, float) or not low <= value <= high:
            raise ValueError('Ajuste inválido: ' + key)
        return float(value)
    rotate = ops.get('rotate', 0)
    if type(rotate) is not int or rotate not in (0, 90, 180, 270):
        raise ValueError('Giro inválido')
    bright, contrast, color = factor('brightness'), factor('contrast'), factor('saturation', 0, 2)
    crop = ops.get('crop')
    if crop is not None:
        if not isinstance(crop, dict) or any(type(crop.get(k)) not in (int, float) for k in 'xywh'):
            raise ValueError('Corte inválido')
        x, y, w, h = (float(crop[k]) for k in 'xywh')
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1.0001 or y + h > 1.0001:
            raise ValueError('Corte fora da imagem')
    erase = clean_erase(ops.get('erase'))
    look = ops.get('look')
    if look is not None:
        if not isinstance(look, dict):
            raise ValueError('Filtro inválido')
        def amount(key, low=0.0):
            value = look.get(key, 0)
            if type(value) not in (int, float) or not low <= value <= 1:
                raise ValueError('Filtro inválido: ' + key)
            return float(value)
        look = {'warmth': amount('warmth', -1.0), 'vignette': amount('vignette'), 'fade': amount('fade'), 'soften': amount('soften')}
        if not any(look.values()):
            look = None
    focus = ops.get('focus')
    if focus is not None:
        def unit(key, low=0.0, high=1.0, optional=False):
            value = focus.get(key) if isinstance(focus, dict) else False
            if value is None and optional:
                return None
            if type(value) not in (int, float) or not low <= value <= high:
                raise ValueError('Foco inválido')
            return float(value)
        focus = {'x': unit('x', optional=True), 'y': unit('y', optional=True), 'r': unit('r', .03, 1), 'sharpen': unit('sharpen'), 'blur': unit('blur')}
        if (focus['x'] is None) != (focus['y'] is None):
            raise ValueError('Foco inválido')
        if not focus['sharpen'] and not (focus['blur'] and focus['x'] is not None):
            focus = None
    try:
        with Image.open(source) as img:
            fmt = img.format
            exif = img.getexif()
            img = ImageOps.exif_transpose(img)
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA' if 'A' in img.getbands() or 'transparency' in img.info else 'RGB')
            if erase:
                img = apply_erase(img, erase)
            if rotate:
                img = img.transpose({90: Image.ROTATE_270, 180: Image.ROTATE_180, 270: Image.ROTATE_90}[rotate])
            if ops.get('flip_h'):
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            if ops.get('flip_v'):
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            if focus:
                img = apply_focus(img, focus)
            if crop is not None:
                W, H = img.size
                box = (round(x * W), round(y * H), min(W, round((x + w) * W)), min(H, round((y + h) * H)))
                if box[2] - box[0] < 16 or box[3] - box[1] < 16:
                    raise ValueError('Corte pequeno demais')
                img = img.crop(box)
            if look:
                img = apply_look(img, look)
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

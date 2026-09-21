from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pathlib import Path
import shutil, uuid, io, base64, os, asyncio

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / 'outputs'
OUTPUTS.mkdir(exist_ok=True)

app = FastAPI(title='Forge AI Mobile', version='0.4.0')
app.mount('/static', StaticFiles(directory=ROOT/'static'), name='static')
app.mount('/outputs', StaticFiles(directory=OUTPUTS), name='outputs')

MAX_BYTES = 12 * 1024 * 1024
ALLOWED = {'.png', '.jpg', '.jpeg', '.webp'}
DEFAULT_MODEL = 'black-forest-labs/FLUX.1-Kontext-dev'

@app.get('/')
def index():
    return FileResponse(ROOT/'static/index.html')

@app.get('/api/health')
def health():
    return {'ok': True, 'version': '0.4.0', 'ai_configured': bool(os.getenv('HF_TOKEN'))}

@app.post('/api/upload')
async def upload(file: UploadFile = File(...)):
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, 'Görsel 12 MB sınırını aşamaz.')
    if not (file.content_type or '').startswith('image/'):
        raise HTTPException(400, 'Sadece görsel yükleyebilirsiniz.')
    try:
        im = Image.open(io.BytesIO(raw)).convert('RGB')
    except Exception:
        raise HTTPException(400, 'Geçersiz görsel.')
    name = f'{uuid.uuid4().hex}.png'
    path = OUTPUTS / name
    im.save(path, 'PNG', optimize=True)
    return {'url': f'/outputs/{name}', 'filename': name, 'width': im.width, 'height': im.height}

def save_image(im: Image.Image):
    name = f'{uuid.uuid4().hex}.png'
    path = OUTPUTS / name
    im.convert('RGB').save(path, 'PNG', optimize=True)
    return f'/outputs/{name}'

def decode_data_url(data: str | None):
    if not data or ',' not in data:
        return None
    try:
        return Image.open(io.BytesIO(base64.b64decode(data.split(',', 1)[1]))).convert('L')
    except Exception:
        return None

def fit_mask(mask, size):
    if mask is None:
        return None
    return mask.resize(size, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(1.5))

def apply_mask(original, edited, mask):
    if mask is None:
        return edited
    return Image.composite(edited, original, mask)

def local_enhance(im, intensity):
    x = ImageEnhance.Contrast(im).enhance(1 + 0.20 * intensity)
    x = ImageEnhance.Color(x).enhance(1 + 0.16 * intensity)
    x = ImageEnhance.Sharpness(x).enhance(1 + 0.45 * intensity)
    return x.filter(ImageFilter.UnsharpMask(radius=1.1, percent=110, threshold=3))

def local_extend(im, ratio):
    if ratio == '9:16':
        target_h = max(im.height, round(im.width * 16 / 9))
        canvas = Image.new('RGB', (im.width, target_h))
        blurred = im.resize((im.width, target_h), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(24))
        canvas.paste(blurred, (0, 0))
        canvas.paste(im, (0, (target_h - im.height)//2))
        return canvas
    pad = max(24, int(min(im.size) * .08))
    return ImageOps.expand(im, border=pad, fill=(16, 19, 27))

async def hf_edit(original: Image.Image, prompt: str, token: str, model: str, steps: int, guidance: float):
    try:
        from huggingface_hub import InferenceClient
    except ImportError:
        raise HTTPException(500, 'AI paketi eksik. requirements.txt ile yeniden kurun.')
    if not token:
        raise HTTPException(400, 'AI kullanmak için Hugging Face token gerekiyor. Ayarlar bölümüne HF token ekleyin veya HF_TOKEN ortam değişkeni tanımlayın.')
    if not prompt.strip():
        raise HTTPException(400, 'AI düzenleme için bir prompt yazın.')
    client = InferenceClient(api_key=token, provider='auto')
    def run():
        return client.image_to_image(
            original,
            prompt=prompt,
            model=model or DEFAULT_MODEL,
            num_inference_steps=max(4, min(int(steps), 40)),
            guidance_scale=max(1.0, min(float(guidance), 12.0)),
        )
    return await asyncio.to_thread(run)

@app.post('/api/generate')
async def generate(
    file: UploadFile = File(...),
    prompt: str = Form(''),
    mode: str = Form('image-edit'),
    mask: str = Form(''),
    intensity: float = Form(0.7),
    output_ratio: str = Form('original'),
    engine: str = Form('ai'),
    model: str = Form(DEFAULT_MODEL),
    steps: int = Form(20),
    guidance: float = Form(3.5),
    hf_token: str = Form(''),
):
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, 'Görsel 12 MB sınırını aşamaz.')
    try:
        original = Image.open(io.BytesIO(raw)).convert('RGB')
    except Exception:
        raise HTTPException(400, 'Geçersiz görsel.')

    intensity = max(0.0, min(float(intensity), 1.0))
    used_engine = 'local'
    edited = original.copy()

    if mode == 'enhance':
        edited = local_enhance(edited, intensity)
    elif mode == 'extend':
        # Reliable mobile-safe extension; true generative outpainting is provider/model dependent.
        edited = local_extend(edited, output_ratio)
    elif engine == 'ai':
        token = (hf_token or os.getenv('HF_TOKEN') or '').strip()
        generated = await hf_edit(original, prompt, token, model, steps, guidance)
        generated = generated.convert('RGB').resize(original.size, Image.Resampling.LANCZOS)
        m = fit_mask(decode_data_url(mask), original.size)
        # If a mask exists, only replace the painted region; otherwise use the AI result globally.
        edited = apply_mask(original, generated, m) if m is not None else generated
        used_engine = 'huggingface-inference-providers'
    else:
        # Offline fallback: subtle color/contrast change, optionally constrained by mask.
        changed = local_enhance(edited, intensity * .45)
        edited = apply_mask(edited, changed, fit_mask(decode_data_url(mask), edited.size))

    if output_ratio == '9:16' and mode not in {'extend'}:
        # Crop/letterbox to the requested mobile ratio without stretching.
        target_w = edited.width
        target_h = round(target_w * 16 / 9)
        if target_h <= edited.height:
            top = (edited.height - target_h)//2
            edited = edited.crop((0, top, edited.width, top + target_h))
        else:
            canvas = Image.new('RGB', (edited.width, target_h), (10, 12, 18))
            canvas.paste(edited, (0, (target_h-edited.height)//2))
            edited = canvas

    url = save_image(edited)
    return {
        'status': 'done', 'url': url, 'mode': mode, 'engine': used_engine,
        'model': model if used_engine != 'local' else 'local',
        'message': 'Sonuç hazır.' if used_engine != 'local' else 'Yerel sonuç hazır.'
    }

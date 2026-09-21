# Forge AI Mobile v0.4

Telefon odaklı, Zorix benzeri AI fotoğraf düzenleme prototipi.

## Gerçek AI motoru
Bu sürüm Hugging Face Inference Providers üzerinden gerçek image-to-image düzenleme kullanabilir. Varsayılan model:
`black-forest-labs/FLUX.1-Kontext-dev`

Bir Hugging Face hesabı ve Inference Providers yetkili token gerekir. Tokenı sunucunun `HF_TOKEN` environment secret'ı olarak tanımlamak en güvenlisidir; arayüzde de geçici olarak girilebilir.

## Yerelde çalıştırma
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
export HF_TOKEN=hf_xxx    # Windows PowerShell: $env:HF_TOKEN="hf_xxx"
uvicorn app.main:app --host 0.0.0.0 --port 7860
```
Telefondan aynı Wi-Fi üzerindeyken bilgisayarın yerel IP'sine `http://192.168.x.x:7860` ile girilebilir.

## Hugging Face Spaces
Bu klasörü Docker Space olarak yükleyin. Space Settings > Secrets bölümüne `HF_TOKEN` ekleyin. Uygulama 7860 portunu dinler.

## Vercel notu
Vercel yalnız frontend için uygundur. Python AI backend'i ayrı bir sunucuda çalıştırın ve frontend'in API adresini buna yönlendirin. En kolay tek sunucu dağıtımı Hugging Face Spaces Docker'dır.

## Özellikler
- Mobil/PWA arayüz
- Dokunmatik maske
- Gerçek image-to-image AI düzenleme
- Maskeli sonuç birleştirme
- Yerel enhance ve extension fallback
- PNG çıktı
- 12 MB yükleme sınırı

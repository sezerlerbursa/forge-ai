# Forge AI — Telefon/PWA prototipi

Bu sürüm iPhone/Android ekranlarına uyarlanmış ve PWA olarak kurulabilir.

## Telefon üzerinde kullanım
1. Projeyi bir HTTPS sunucuda çalıştırın (veya aynı FastAPI uygulamasını internete açın).
2. Safari/Chrome ile siteyi açın.
3. iPhone'da Paylaş → Ana Ekrana Ekle seçeneğini kullanın.
4. Uygulama tam ekran PWA olarak açılır.

## Gerçek AI motoru
Telefon tarayıcısı arayüzü çalıştırır; ağır diffusion modeli sunucuda çalıştırılmalıdır. `localStorage` içindeki `forge_api_base` değeri ile ayrı bir backend adresi tanımlanabilir.

Örnek tarayıcı konsolu:
`localStorage.setItem('forge_api_base','https://SUNUCU-ADRESI')`

Mevcut backend prototip modunda çalışır. Sonraki adım aynı `/api/generate` endpoint'ine gerçek FLUX/SDXL/ComfyUI inpainting motoru bağlamaktır.

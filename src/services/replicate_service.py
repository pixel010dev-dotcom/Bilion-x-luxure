"""Image generation service — Replicate SDXL (paid) com fallback Pollinations.ai (free)."""
import os
import logging
import httpx
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.prompt_enhancer import enhance_image_prompt

logger = logging.getLogger(__name__)

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN") or os.environ.get("REPLICATE_API_KEY", "")

MODEL = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"


def _try_replicate(prompt: str, image_url: str = None) -> dict:
    """Tenta gerar via Replicate SDXL (precisa de creditos)."""
    if not REPLICATE_API_TOKEN:
        return {"error": "no_key"}

    import replicate
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)

    # Prompt turbinado +18
    enhanced = enhance_image_prompt(prompt, ref_has_image=bool(image_url))

    input_data = {
        "prompt": enhanced,
        "negative_prompt": "ugly, blurry, low quality, deformed, disfigured, nude, nsfw",
        "width": 768,
        "height": 1024,
        "num_inference_steps": 25,
        "guidance_scale": 7.5,
    }
    if image_url:
        input_data["image"] = image_url

    output = client.run(MODEL, input=input_data)
    if output and len(output) > 0:
        return {"url": str(output[0]), "success": True, "engine": "replicate"}
    return {"error": "empty"}


def _try_pollinations(prompt: str) -> dict:
    """Fallback gratuito via Pollinations.ai — sem API key, sem custo."""
    try:
        import urllib.parse

        # Prompt turbinado +18
        enhanced = enhance_image_prompt(prompt)
        encoded = urllib.parse.quote(enhanced[:500])
        image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=1024&nofeed=true"

        # Verifica se o servidor responde (com request menor pra ser rapido)
        with httpx.Client(timeout=10) as c:
            r = c.get(image_url)
            if r.status_code == 200:
                return {"url": image_url, "success": True, "engine": "pollinations", "fallback": True}
            return {"error": f"pollinations status {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def generate_image(prompt: str, negative_prompt: str = None, image_url: str = None) -> dict:
    """Gera imagem: tenta Replicate, fallback Pollinations (free)."""
    # 1. Tenta Replicate (se tiver token e creditos)
    if REPLICATE_API_TOKEN:
        try:
            result = _try_replicate(prompt, image_url)
            if result.get("success"):
                return result
            # Se for erro de credito (402), cai no fallback
            error = result.get("error", "")
            logger.warning(f"Replicate falhou ({error}), tentando fallback gratuito...")
        except Exception as e:
            logger.warning(f"Replicate exception: {e}, tentando fallback...")

    # 2. Fallback gratuito — Pollinations.ai
    # Nota: img2img nao funciona no fallback (Pollinations nao suporta)
    if image_url:
        logger.info("Fallback nao suporta img2img — gerando sem referencia")
    return _try_pollinations(prompt)

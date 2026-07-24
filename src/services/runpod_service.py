"""RunPod API service for video generation (Wan 2.1)."""
import os
import json
import time
import requests
import logging

logger = logging.getLogger(__name__)

RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
RUNPOD_ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "")

WAN_COST_PER_SECOND = 0.003  # USD


def generate_video(prompt: str, duration: str = "4s", negative_prompt: str = None) -> dict:
    """
    Generate a video using RunPod Wan 2.1.
    duration: '4s' or '8s'
    Falls back to error message if not configured.
    """
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        return {"error": "RunPod não configurado. Preciso de RUNPOD_API_KEY e RUNPOD_ENDPOINT_ID no .env"}

    num_frames = 49 if duration == "4s" else 81  # ~12fps

    try:
        # 1. Iniciar job no RunPod serverless
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "input": {
                "prompt": prompt,
                "negative_prompt": negative_prompt or "",
                "num_frames": num_frames,
                "width": 512,
                "height": 512,
                "num_inference_steps": 20,
                "guidance_scale": 5.0,
            }
        }

        run_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"
        resp = requests.post(run_url, headers=headers, json=payload, timeout=300)

        if resp.status_code != 200:
            logger.error(f"RunPod error: {resp.status_code} {resp.text}")
            return {"error": f"RunPod retornou {resp.status_code}"}

        result = resp.json()

        if result.get("status") == "COMPLETED" and result.get("output"):
            video_url = result["output"]
            if isinstance(video_url, list) and len(video_url) > 0:
                video_url = video_url[0]
            return {"url": str(video_url), "success": True}
        else:
            error = result.get("error", "Erro desconhecido do RunPod")
            logger.error(f"RunPod fail: {result}")
            return {"error": str(error)}

    except requests.exceptions.Timeout:
        return {"error": "RunPod timeout — geração de vídeo demorou demais"}
    except Exception as e:
        logger.error(f"RunPod exception: {e}")
        return {"error": str(e)}


def generate_video_with_fallback(prompt: str, duration: str = "4s") -> dict:
    """Tenta RunPod primeiro, fallback Replicate."""
    # Tenta RunPod
    result = generate_video(prompt, duration)

    if result.get("success"):
        logger.info(f"Vídeo gerado via RunPod: {duration}")
        return result

    # Fallback: Replicate (modelo de vídeo)
    logger.warning(f"RunPod falhou, tentando Replicate fallback: {result.get('error')}")
    try:
        import replicate
        from src.services.replicate_service import REPLICATE_API_KEY

        if not REPLICATE_API_KEY:
            return {"error": "Sem fallback — Replicate também não configurado"}

        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_KEY

        # Usar um modelo de vídeo no Replicate (ex: stability-ai/stable-video-diffusion)
        model = "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438"
        output = replicate.run(
            model,
            input={
                "prompt": prompt,
                "num_frames": 49 if duration == "4s" else 81,
                "fps": 12,
            },
        )

        if output and len(output) > 0:
            video_url = str(output[0]) if isinstance(output, list) else str(output)
            return {"url": video_url, "success": True, "fallback": True}

        return {"error": "Replicate não gerou vídeo"}

    except Exception as e:
        logger.error(f"Fallback error: {e}")
        return {"error": f"RunPod e fallback falharam: {e}"}

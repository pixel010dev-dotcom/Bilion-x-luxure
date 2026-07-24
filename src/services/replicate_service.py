"""Replicate API service for image generation."""
import os
import replicate
import logging

logger = logging.getLogger(__name__)

REPLICATE_API_KEY = os.environ.get("REPLICATE_API_KEY", "")

# Using Stable Diffusion XL - fast and cheap (~$0.002/image)
MODEL = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"


def generate_image(prompt: str, negative_prompt: str = None) -> dict:
    """Generate an image using Replicate SDXL. Returns dict with url or error."""
    if not REPLICATE_API_KEY:
        return {"error": "Replicate API key not configured"}

    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_KEY

    try:
        input_data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "ugly, blurry, low quality, deformed, disfigured",
            "width": 768,
            "height": 1024,
            "num_inference_steps": 25,
            "guidance_scale": 7.5,
        }

        output = replicate.run(MODEL, input=input_data)

        if output and len(output) > 0:
            return {"url": str(output[0]), "success": True}
        else:
            return {"error": "No image generated"}

    except Exception as e:
        logger.error(f"Replicate error: {e}")
        return {"error": str(e)}

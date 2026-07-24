"""Prompt enhancer — adapta o contexto do usuario pro modelo alvo, detectando tom +18."""
import logging
import re

logger = logging.getLogger(__name__)

# Palavras que indicam intencao +18 / sensual
ADULT_KEYWORDS = {
    "anal", "sexo", "transando", "penetrando", "gozando", "gemendo",
    "nua", "pelada", "nude", "nu", "naked", "pau", "buceta", "vagina",
    "lingerie", "sensual", "erotic", "erotico", "hot", "gostosa",
    "selvagem", "tesao", "tesão", "exciting", "provocante",
    "provocative", "delicia", "delícia", "tasty", "sexy",
    "intimate", "intimo", "intima", "passional", "passionate",
    "na cama", "no sofa", "de quatro", "doggy", "missionario",
    "sugando", "chupando", "mamando", "boquete", "oral",
}

# Palavras que indicam retrato / close-up
CLOSEUP_KEYWORDS = {
    "rosto", "face", "cara", "close", "closeup", "retrato",
    "portrait", "cabeca", "cabeça", "olhos", "olho",
}


def detect_tone(user_input: str) -> str:
    """Detecta o tom do input: 'adult', 'portrait', ou 'general'."""
    lower = user_input.lower()
    words = set(lower.split())

    # Checa se tem palavra +18
    if any(ak in lower for ak in ADULT_KEYWORDS):
        return "adult"

    # Checa se tem palavra de close-up / retrato
    if any(ck in lower for ck in CLOSEUP_KEYWORDS):
        return "portrait"

    return "general"


def enhance_prompt(user_input: str, model: str = "sdxl", style: str = "realistic", ref_has_image: bool = False) -> str:
    """Expande o contexto do usuario em prompt otimizado pro modelo alvo.

    Detecta automaticamente se o tom e +18 e aplica descritores apropriados.
    """
    if not user_input:
        return user_input

    user_input = user_input.strip().rstrip(".,!?")
    model = model.lower()
    tone = detect_tone(user_input)

    # Se tem imagem de referencia, o prompt descreve a alteracao
    if not ref_has_image:
        base = user_input
    else:
        base = user_input

    expanded = _apply_model_template(base, model, tone, style)

    logger.debug(f"Prompt enhancer [{tone}]: '{user_input[:50]}' -> '{expanded[:80]}...'")
    return expanded


def _apply_model_template(prompt: str, model: str, tone: str, style: str) -> str:
    """Aplica template com base no modelo, tom e estilo."""

    if tone == "adult":
        return _adult_template(prompt, model)
    elif tone == "portrait":
        return _portrait_template(prompt, model)
    else:
        return _general_template(prompt, model, style)


def _adult_template(prompt: str, model: str) -> str:
    """Prompt para conteudo +18 / sensual."""
    base = (
        f"{prompt}, intimate atmosphere, sensual mood, "
        f"soft dramatic lighting, high detail, sharp focus, "
        f"masterpiece, best quality, 8k"
    )
    if model in ("wan", "runpod"):
        base += ", cinematic video, fluid motion, slow sensual movement"
    return base


def _portrait_template(prompt: str, model: str) -> str:
    """Prompt para retratos / close-ups."""
    base = (
        f"{prompt}, professional portrait photography, "
        f"natural lighting, sharp focus on eyes, detailed skin texture, "
        f"shallow depth of field, masterpiece, 8k"
    )
    return base


def _general_template(prompt: str, model: str, style: str) -> str:
    """Prompt generico com estilo."""
    if model in ("sdxl", "replicate"):
        base = (
            f"{prompt}, professional photography, natural lighting, "
            f"high detail, sharp focus, masterpiece, best quality, 8k"
        )
    elif model in ("wan", "runpod"):
        base = (
            f"{prompt}, cinematic video, smooth motion, "
            f"professional lighting, masterpiece, 4k"
        )
    else:
        base = f"{prompt}, high quality, detailed"
    return base


def enhance_image_prompt(user_input: str, style: str = "realistic", ref_has_image: bool = False) -> str:
    return enhance_prompt(user_input, "sdxl", style, ref_has_image)


def enhance_video_prompt(user_input: str, style: str = "cinematic") -> str:
    return enhance_prompt(user_input, "wan", style)

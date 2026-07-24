"""Utilitarios para processamento de imagens do Telegram."""
import base64
import io
import logging
import httpx

logger = logging.getLogger(__name__)


async def download_photo_to_data_url(file) -> str:
    """Baixa uma foto do Telegram e converte pra data URL (base64)."""
    file_bytes = io.BytesIO()
    await file.download_to_memory(file_bytes)
    file_bytes.seek(0)
    b64 = base64.b64encode(file_bytes.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"

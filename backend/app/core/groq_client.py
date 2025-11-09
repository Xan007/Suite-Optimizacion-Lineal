import base64
import json
from typing import Optional, List, Union, Dict, Any, BinaryIO
from groq import Groq
from app.core.logger import logger
from app.core.config import settings


class GroqClient:
    """Cliente para la API de Groq con soporte para texto, imágenes y prompts de sistema."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or settings.GROQ_MODEL
        self.client = Groq(api_key=api_key)
        self.system_prompt: Optional[str] = None

    # ------------------------------------------------------------------------
    # Configuración
    # ------------------------------------------------------------------------
    def set_system_prompt(self, prompt: str) -> None:
        """Define el prompt de sistema para futuras llamadas."""
        self.system_prompt = prompt

    # ------------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------------
    @staticmethod
    def _encode_image_file(file: Union[BinaryIO, bytes]) -> str:
        """Codifica un archivo de imagen a base64 (acepta bytes o archivo binario)."""
        try:
            if isinstance(file, bytes):
                content = file
            else:
                content = file.read()
            return base64.b64encode(content).decode("utf-8")
        except Exception as e:
            logger.error("Error codificando imagen a base64", exc_info=True)
            raise

    # ------------------------------------------------------------------------
    # Chat general
    # ------------------------------------------------------------------------
    def chat(
        self,
        user_prompt: str,
        *,
        images: Optional[List[Union[bytes, BinaryIO]]] = None,
        image_urls: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Envía un mensaje al modelo Groq con soporte opcional para imágenes.

        Args:
            user_prompt: Texto del usuario
            images: Lista de archivos binarios o bytes
            image_urls: Lista de URLs de imágenes
            system_prompt: Prompt de sistema adicional (opcional)
            temperature: Temperatura de la generación
            max_tokens: Límite de tokens

        Returns:
            dict con claves: success, content, tokens, raw
        """
        try:
            messages = []

            # Prompt del sistema (global o puntual)
            if self.system_prompt or system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt or self.system_prompt
                })

            # Contenido del usuario
            content = [{"type": "text", "text": user_prompt}]

            # Agregar imágenes locales (como bytes)
            if images:
                for img in images:
                    base64_img = self._encode_image_file(img)
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_img}"}
                    })

            # Agregar URLs de imágenes
            if image_urls:
                for url in image_urls:
                    content.append({"type": "image_url", "image_url": {"url": url}})

            messages.append({"role": "user", "content": content})

            logger.info(f"Enviando mensaje a Groq (modelo={self.model})")

            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            choice = chat_completion.choices[0].message
            tokens_used = getattr(chat_completion.usage, "total_tokens", 0)

            return {
                "success": True,
                "content": choice.content,
                "tokens": tokens_used,
                "raw": chat_completion
            }

        except Exception as e:
            logger.error("Error en GroqClient.chat", exc_info=True)
            return {"success": False, "error": str(e)}


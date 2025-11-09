"""
Prompts para análisis de problemas de optimización lineal.
Cada prompt tiene un nombre descriptivo para ser seleccionado dinámicamente.

Prompts disponibles:
- "basic": Análisis básico con validación de linealidad
- "detailed": Análisis detallado con guía paso a paso
"""

from app.prompts.basic_analysis import BASIC_ANALYSIS

__all__ = [
    "BASIC_ANALYSIS",
    "get_prompt",
    "list_prompts",
]

# Mapeo de nombres a prompts - usando ID pero con nombres descriptivos
PROMPTS = {
    "basic": BASIC_ANALYSIS,
}


def get_prompt(prompt_name: str = "basic") -> str:
    """
    Obtiene el prompt según su nombre descriptivo.
    
    Args:
        prompt_name: Nombre del prompt ("basic", "detailed", etc.)
        
    Returns:
        String con el prompt completo
        
    Raises:
        ValueError si el nombre no es válido
    """
    if prompt_name not in PROMPTS:
        available = ", ".join(PROMPTS.keys())
        raise ValueError(f"Prompt '{prompt_name}' no encontrado. Disponibles: {available}")
    
    return PROMPTS[prompt_name]


def list_prompts() -> list:
    """Retorna lista de nombres de prompts disponibles."""
    return list(PROMPTS.keys())


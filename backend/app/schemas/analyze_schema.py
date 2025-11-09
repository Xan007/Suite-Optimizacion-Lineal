from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.core.config import settings


class MathematicalModel(BaseModel):
    """Modelo matemático con función objetivo, restricciones, variables y contexto resumido."""
    
    objective_function: str = Field(..., description="Función objetivo (ej: '3*x + 2*y')")
    constraints: List[str] = Field(default_factory=list, description="Lista de restricciones textuales (ej: 'x + y <= 10')")
    variables: Dict[str, str] = Field(default_factory=dict, description="Variables de decisión con sus descripciones (ej: {'x': 'Cantidad de producto A', 'y': 'Cantidad de producto B'})")
    objective: str = Field(default="max", description="Objetivo: 'max' o 'min'")
    context: str = Field(default="", description="Contexto resumido del problema para posterior análisis con IA")
    
    class Config:
        json_schema_extra = {
            "example": {
                "objective_function": "3*x + 2*y",
                "objective": "max",
                "constraints": ["x + y <= 10", "x >= 0", "y >= 0"],
                "variables": {
                    "x": "Cantidad de producto A",
                    "y": "Cantidad de producto B"
                },
                "context": "Problema de producción: maximizar ganancias de dos productos sujeto a límite de horas disponibles"
            }
        }


class AnalyzeRequest(BaseModel):
    """Solicitud para analizar un problema mediante texto."""
    
    problem: str = Field(..., description="Descripción del problema a analizar")
    api_key: Optional[str] = Field(default=None, description="API key del usuario (opcional)")
    groq_model: Optional[str] = Field(default=settings.GROQ_MODEL, description="Modelo de Groq a usar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "problem": "Una fábrica produce dos productos A y B. El producto A requiere 2 horas y genera $3 de ganancia. El producto B requiere 1 hora y genera $2 de ganancia. Se tienen 10 horas disponibles. ¿Cuántos productos de cada uno deben producir para maximizar la ganancia?",
                "api_key": "user-api-key-optional",
                "groq_model": settings.GROQ_MODEL
            }
        }


class AnalyzeImageRequest(BaseModel):
    """Solicitud para analizar un problema desde una imagen."""
    
    problem_description: Optional[str] = Field(default=None, description="Descripción adicional del problema (opcional)")
    api_key: Optional[str] = Field(default=None, description="API key del usuario (opcional)")
    groq_model: Optional[str] = Field(default=settings.GROQ_MODEL, description="Modelo de Groq a usar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "problem_description": "Foto de un problema de optimización escrito en papel",
                "api_key": "user-api-key-optional",
                "groq_model": settings.GROQ_MODEL
            }
        }


class ProblemRepresentations(BaseModel):
    """Todas las representaciones del problema."""
    
    canonical: Optional[Dict[str, Any]] = Field(default=None, description="Forma canónica")
    standard: Optional[Dict[str, Any]] = Field(default=None, description="Forma estándar")
    matrix: Optional[Dict[str, Any]] = Field(default=None, description="Forma matricial")
    dual: Optional[Dict[str, Any]] = Field(default=None, description="Problema dual")


class AnalyzeResponse(BaseModel):
    """Respuesta del análisis con el modelo y todas sus representaciones."""
    
    raw_analysis: str = Field(..., description="Análisis textual de Groq")
    mathematical_model: MathematicalModel = Field(..., description="Modelo matemático extraído (forma canónica)")
    representations: Optional[ProblemRepresentations] = Field(default=None, description="Representaciones: standard, matrix, dual")
    groq_model: str = Field(..., description="Modelo de Groq usado")
    is_linear: bool = Field(default=True, description="Indica si el problema es lineal")
    
    class Config:
        json_schema_extra = {
            "example": {
                "raw_analysis": "Este es un problema de programación lineal...",
                "mathematical_model": {
                    "objective_function": "3*x + 2*y",
                    "objective": "max",
                    "constraints": ["x + y <= 10", "x >= 0", "y >= 0"],
                    "variables": ["x", "y"]
                },
                "representations": {
                    "canonical": {},
                    "standard": {},
                    "matrix": {},
                    "dual": {}
                },
                "groq_model": "mixtral-8x7b-32768",
                "is_linear": True
            }
        }

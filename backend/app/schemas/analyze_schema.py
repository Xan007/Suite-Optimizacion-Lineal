from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.api.docs import (
    MATHEMATICAL_MODEL_EXAMPLE,
    ANALYZE_RESPONSE_EXAMPLE,
    VALIDATE_MODEL_RESPONSE_EXAMPLE,
)


class MathematicalModel(BaseModel):
    """Modelo matemático con función objetivo, restricciones, variables y contexto resumido."""
    
    objective_function: str = Field(..., description="Función objetivo (ej: '3*x1 + 2*x2')")
    constraints: List[str] = Field(default_factory=list, description="Lista de restricciones textuales (ej: ['2*x1 + x2 <= 10', 'x1 >= 0'])")
    variables: Dict[str, str] = Field(default_factory=dict, description="Variables de decisión con sus descripciones (ej: {'x1': 'Unidades producto A', 'x2': 'Unidades producto B'})")
    objective: str = Field(default="max", description="Objetivo: 'max' para maximizar o 'min' para minimizar")
    context: str = Field(default="", description="Contexto resumido del problema para posterior análisis con IA")
    
    class Config:
        json_schema_extra = {
            "example": {
                "objective_function": "3*x1 + 2*x2",
                "objective": "max",
                "constraints": ["2*x1 + x2 <= 10"],
                "variables": {
                    "x1": "Unidades de producto A a producir",
                    "x2": "Unidades de producto B a producir"
                },
                "context": "Fábrica con 2 productos. Producto A: 2h de trabajo y $3 ganancia. Producto B: 1h de trabajo y $2 ganancia. Máximo 10 horas disponibles. Objetivo: maximizar ganancia total."
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
                "problem": "Una fábrica produce dos productos A y B. El producto A requiere 2 horas de trabajo y genera $3 de ganancia por unidad. El producto B requiere 1 hora de trabajo y genera $2 de ganancia por unidad. Se dispone de un máximo de 10 horas de trabajo. ¿Cuántas unidades de cada producto deben producir para maximizar la ganancia total?",
                "api_key": None,
                "groq_model": "openai/gpt-oss-20b"
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
    big_m: Optional[Dict[str, Any]] = Field(default=None, description="Método de la Gran M (para restricciones >= y =)")


class AnalyzeResponse(BaseModel):
    """Respuesta del análisis con el modelo y todas sus representaciones."""
    
    raw_analysis: str = Field(..., description="Análisis textual de Groq sobre el problema")
    mathematical_model: MathematicalModel = Field(..., description="Modelo matemático extraído (forma canónica)")
    representations: Optional[ProblemRepresentations] = Field(default=None, description="Representaciones: canonical, standard, matrix, dual")
    groq_model: str = Field(..., description="Modelo de Groq usado")
    is_linear: bool = Field(default=True, description="Indica si el problema es lineal")
    
    class Config:
        json_schema_extra = {
            "example": {
                "raw_analysis": "Este es un problema de programación lineal de maximización. Se trata de una situación de producción donde una fábrica necesita determinar la cantidad de dos productos a manufacturar para maximizar ganancias sujeto a restricciones de horas disponibles...",
                "mathematical_model": {
                    "objective_function": "3*x1 + 2*x2",
                    "objective": "max",
                    "constraints": ["2*x1 + x2 <= 10"],
                    "variables": {
                        "x1": "Unidades de producto A",
                        "x2": "Unidades de producto B"
                    },
                    "context": "Problema de producción con 2 productos"
                },
                "representations": {
                    "canonical": {
                        "form": "canonical",
                        "objective": "max",
                        "objective_function": "3*x1 + 2*x2",
                        "constraints": [
                            {"expression": "2*x1 + x2", "operator": "<=", "rhs": 10.0}
                        ],
                        "variables": {"x1": "Unidades de producto A", "x2": "Unidades de producto B"}
                    },
                    "standard": {
                        "form": "standard",
                        "objective": "max",
                        "objective_function": "3*x1 + 2*x2",
                        "constraints": [
                            {"expression": "2*x1 + x2 + s1", "operator": "=", "rhs": 10.0}
                        ],
                        "slack_variables": {"s1": "Holgura 1"},
                        "non_negativity": [
                            {"expression": "x1", "operator": ">=", "rhs": 0},
                            {"expression": "x2", "operator": ">=", "rhs": 0},
                            {"expression": "s1", "operator": ">=", "rhs": 0}
                        ]
                    },
                    "matrix": {
                        "form": "matrix",
                        "objective": "max",
                        "A": [[2, 1]],
                        "b": [[10]],
                        "c": [[3, 2]],
                        "variables": ["x1", "x2"],
                        "dimensions": {"constraints": 1, "variables": 2},
                        "note": "Non-negativity conditions (x >= 0) are implicit"
                    },
                    "dual": {
                        "form": "dual",
                        "objective": "min",
                        "objective_function": "10.0*y1",
                        "constraints": [
                            {"expression": "2*y1", "operator": ">=", "rhs": 3.0},
                            {"expression": "y1", "operator": ">=", "rhs": 2.0}
                        ],
                        "variables": {"y1": "Dual variable for constraint 1"},
                        "primal_objective": "max",
                        "primal_variables_count": 2,
                        "dual_variables_count": 1
                    },
                    "big_m": {
                        "form": "big_m",
                        "objective": "max",
                        "objective_function": "3*x1 + 2*x2",
                        "constraints": [
                            {"expression": "2*x1 + x2 + s1", "operator": "=", "rhs": 10.0}
                        ],
                        "slack_variables": {"s1": "Holgura 1"},
                        "artificial_variables": {},
                        "non_negativity": [
                            {"expression": "x1", "operator": ">=", "rhs": 0},
                            {"expression": "x2", "operator": ">=", "rhs": 0},
                            {"expression": "s1", "operator": ">=", "rhs": 0}
                        ],
                        "M": "Constante grande usada para penalizar las variables artificiales (típicamente 10^6)"
                    }
                },
                "groq_model": "openai/gpt-oss-20b",
                "is_linear": True
            }
        }

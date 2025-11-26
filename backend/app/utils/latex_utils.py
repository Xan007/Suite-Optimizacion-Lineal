"""
Utilidades para conversión de expresiones matemáticas a formato LaTeX.
"""

import sympy as sp
from typing import Optional, Dict
from app.core.logger import logger


def format_expression_to_latex(expr_str: str) -> str:
    """Convierte una expresión matemática a formato LaTeX.
    
    Args:
        expr_str: Expresión en formato SymPy como string
        
    Returns:
        String con la expresión en formato LaTeX
    """
    try:
        expr = sp.sympify(expr_str)
        return sp.latex(expr)
    except Exception as e:
        logger.warning(f"Error al convertir a LaTeX: {e}")
        return expr_str


def convert_constraint_to_latex(constraint_str: str) -> Optional[str]:
    """Convierte una restricción al formato LaTeX.
    
    Args:
        constraint_str: String de la restricción en formato "expr1 op expr2"
        
    Returns:
        String en formato LaTeX o None si hay error
    """
    try:
        for op in ["<=", ">=", "="]:
            if op in constraint_str:
                parts = constraint_str.split(op, 1)
                if len(parts) == 2:
                    lhs_latex = format_expression_to_latex(parts[0].strip())
                    rhs_latex = format_expression_to_latex(parts[1].strip())
                    op_symbol = r"\leq" if op == "<=" else (r"\geq" if op == ">=" else "=")
                    return f"{lhs_latex} {op_symbol} {rhs_latex}"
                break
    except Exception as e:
        logger.warning(f"Error al convertir restricción a LaTeX: {e}")
    return None


def generate_nonnegative_latex_conditions(variables: Dict[str, str]) -> list:
    """Genera condiciones de no-negatividad en formato LaTeX.
    
    Args:
        variables: Dict de variables del modelo
        
    Returns:
        Lista con condiciones de no-negatividad en LaTeX
    """
    conditions = []
    for var_name in variables.keys():
        conditions.append(f"{var_name} \\geq 0")
    return conditions

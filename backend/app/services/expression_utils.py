"""
Utilidades para manipulación y normalización de expresiones algebraicas.
"""

import re
import ast
from app.core.logger import logger


def insert_multiplication(expr_str: str) -> str:
    """
    Inserta operadores de multiplicación explícitos donde falten.
    IMPORTANTE: Respeta nombres de variables como x1, x2, y1, etc.
    
    Ejemplos:
        "3x" -> "3*x"
        "2(x+y)" -> "2*(x+y)"
        "3x1" -> "3*x1"
        "2x2" -> "2*x2"
    
    Args:
        expr_str: Expresión algebraica como string
        
    Returns:
        Expresión con multiplicaciones explícitas
    """
    # Convertir a string si no lo es
    expr_str = str(expr_str)
    result = ""
    for i, char in enumerate(expr_str):
        result += char
        if i < len(expr_str) - 1:
            next_char = expr_str[i + 1]
            
            # Si actual es dígito y siguiente es letra: "3x" -> "3*x"
            if char.isdigit() and next_char.isalpha():
                # PERO: si anterior es letra, significa que estamos dentro de un nombre de variable
                # Ej: "x1" - no añadir * entre x y 1
                if i == 0 or not expr_str[i - 1].isalpha():
                    result += "*"
            
            # Si actual es dígito y siguiente es ( : "2(...)" -> "2*(...)"
            elif char.isdigit() and next_char == "(":
                result += "*"
            
            # Si actual es ) y siguiente es (, ej: "(...)(...)""
            elif char == ")" and next_char == "(":
                result += "*"
            
            # Si actual es letra y siguiente es ( : "x(" -> "x*("
            elif char.isalpha() and next_char == "(":
                result += "*"
    
    return result


def clean_sympy_expression(expr_str: str) -> str:
    """
    Limpia la representación de una expresión SymPy.
    Elimina multiplicaciones innecesarias (*) que no están entre coeficiente y variable.
    
    Ejemplos:
        "1*x1" -> "x1"
        "4*x*1" -> "4*x1"
        "x*1 + x*2" -> "x1 + x2"
        "6*x*2" -> "6*x2"
    
    Args:
        expr_str: String de expresión SymPy con múltiples * innecesarios
        
    Returns:
        Expresión limpia con * solo donde corresponde (coef * var)
    """
    # Paso 1: Remover * entre una variable y sus índices consecutivos
    # "x*1" -> "x1", "x*2" -> "x2", etc.
    cleaned = re.sub(r'([a-zA-Z_]+)\*(\d+)', r'\1\2', expr_str)
    
    # Paso 2: Remover * después de coeficientes numéricos que son solo "1" cuando va a variable
    # Pero solo si el siguiente carácter es una letra (variable)
    # "1*x1" -> "x1" (porque coef 1 es implícito)
    # Necesitamos ser cuidadosos aquí
    
    # Paso 3: Remover coeficientes 1 explícitos (excepto si es el único término)
    # "1*x1" -> "x1" pero solo en contexto de suma/resta
    # Para esto buscamos "1*" al inicio o después de +/-
    cleaned = re.sub(r'(\+|\s)1\*', r'\1', cleaned)  # "+ 1*x" -> "+ x"
    cleaned = re.sub(r'^1\*', '', cleaned)  # "1*x" al inicio -> "x"
    cleaned = re.sub(r'(\-\s)1\*', r'\1', cleaned)  # "- 1*x" -> "- x"
    
    return cleaned


def matrix_to_nested_list(matrix_str: str) -> list:
    """
    Convierte string de SymPy Matrix a nested list (array JSON).
    
    Ejemplos:
        "Matrix([[2, 1]])" -> [[2, 1]]
        "Matrix([[10.0000000000000]])" -> [[10]]
        "Matrix([[3], [2]])" -> [[3], [2]]
    
    Args:
        matrix_str: String de representación Matrix de SymPy
        
    Returns:
        Nested list que puede ser convertida a JSON
    """
    import json
    
    # Remover "Matrix(" al inicio y ")" al final
    if matrix_str.startswith("Matrix("):
        matrix_str = matrix_str[7:-1]  # Remover "Matrix(" y ")"
    
    # Limpiar números decimales que son enteros
    matrix_str = re.sub(r'(\d+)\.0+(?![0-9])', r'\1', matrix_str)
    
    # Reemplazar [ y ] para que sea valid JSON
    # Pero primero necesitamos procesar como Python literal
    try:
        # Usar ast.literal_eval para convertir a Python list
        matrix_list = ast.literal_eval(matrix_str)
        return matrix_list
    except (ValueError, SyntaxError) as e:
        # Si falla, registrar el error y retornar lista vacía
        logger.warning(f"No se pudo convertir matriz a list: {matrix_str}. Error: {e}")
        return []


def reorder_expression_terms(expr_str: str, original_vars: list, slack_vars: list) -> str:
    """
    Reordena términos de una expresión para poner variables originales primero, luego holguras.
    
    Ejemplos:
        "s1 + 2*x1 + x2" -> "2*x1 + x2 + s1"
        "s2 - 3*x1 + x2" -> "x2 - 3*x1 + s2"
    
    Args:
        expr_str: Expresión como string
        original_vars: Lista de nombres de variables originales ["x1", "x2"]
        slack_vars: Lista de nombres de variables de holgura ["s1", "s2"]
        
    Returns:
        Expresión con términos reordenados
    """
    # Si no hay expresión o está vacía, retornar tal cual
    if not expr_str or not original_vars:
        return expr_str
    
    # Dividir por + y - manteniendo los operadores
    import re
    # Patrón para dividir pero mantener operadores
    parts = re.split(r'(?<=[0-9a-zA-Z_\)])\s*([+-])\s*', expr_str)
    
    terms = []
    current_sign = "+"
    
    for i, part in enumerate(parts):
        if part in ["+", "-"]:
            current_sign = part
        elif part.strip():
            terms.append((current_sign, part.strip()))
    
    # Separar términos por tipo
    original_terms = []
    slack_terms = []
    
    for sign, term in terms:
        # Verificar si el término contiene variable de holgura
        is_slack = any(slack in term for slack in slack_vars)
        if is_slack:
            slack_terms.append((sign, term))
        else:
            original_terms.append((sign, term))
    
    # Reconstruir: originales primero, luego holguras
    result_terms = original_terms + slack_terms
    
    if not result_terms:
        return expr_str
    
    # Construir string resultado
    result = result_terms[0][1]  # Primer término sin signo
    for sign, term in result_terms[1:]:
        result += f" {sign} {term}"
    
    return result


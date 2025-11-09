"""
Utilidades para manipulación y normalización de expresiones algebraicas.
"""

import re


def insert_multiplication(expr_str: str) -> str:
    """
    Inserta operadores de multiplicación explícitos donde falten.
    
    Ejemplos:
        "3x" -> "3*x"
        "2(x+y)" -> "2*(x+y)"
        "xy" -> "x*y"
    
    Args:
        expr_str: Expresión algebraica como string
        
    Returns:
        Expresión con multiplicaciones explícitas
    """
    result = ""
    for i, char in enumerate(expr_str):
        result += char
        if i < len(expr_str) - 1:
            next_char = expr_str[i + 1]
            # Si actual es dígito y siguiente es letra, o actual es ) y siguiente es (
            if (char.isdigit() and next_char.isalpha()) or (char == ")" and next_char == "("):
                result += "*"
            # Si actual es letra y siguiente es ( o dígito
            if char.isalpha() and (next_char == "(" or next_char.isdigit()):
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


"""
Procesador de problemas raw en formato estructurado con SymPy.
Normaliza variables, restricciones y función objetivo.
"""

from typing import Dict, Optional, Any
import sympy as sp
from sympy import Symbol
from sympy.core.relational import Relational

from app.core.logger import logger
from app.services.expression_utils import insert_multiplication


class ProblemProcessor:
    """
    Convierte un problema raw (JSON desde Groq) en un formato normalizado
    con expresiones SymPy.
    
    Estructura interna (self.problem):
    {
        'variables': {Symbol('x'): 'descripción', ...},
        'constraints': [(expr, sign, rhs, original_op), ...],  # original_op = operador antes de normalizar
        'objective_function': Expr SymPy,
        'objective': 'max' o 'min'
    }
    """

    def __init__(self):
        self.problem: Dict[str, Any] = {}
        self.raw_problem: Dict[str, Any] = {}

    def set_raw_problem(self, raw_problem: Dict) -> None:
        """Establece el problema raw a procesar."""
        self.raw_problem = raw_problem

    def get_symbols(self) -> Dict[str, Symbol]:
        """
        Retorna diccionario de símbolos SymPy desde las variables del problema.
        
        Returns:
            Dict con formato {'x': Symbol('x'), 'y': Symbol('y'), ...}
        """
        if "variables" not in self.problem or not self.problem["variables"]:
            return {}
        return {str(symbol): symbol for symbol in self.problem["variables"].keys()}

    def process(self) -> bool:
        """
        Procesa el problema raw completamente.
        
        Orden de procesamiento:
        1. Variables de decisión
        2. Restricciones
        3. Función objetivo
        4. Tipo de objetivo (max/min)
        
        Returns:
            True si el procesamiento fue exitoso
            
        Raises:
            Exception si hay error durante el procesamiento
        """
        try:
            self.problem["constraints"] = []
            self.problem["variables"] = {}
            self.problem["objective_function"] = None
            self.problem["objective"] = "max"
            self.problem["context"] = self.raw_problem.get("context", "")

            self._process_variables()
            self._process_constraints()
            self._process_objective_function()
            self._process_objective_mode()

            logger.info("Problema procesado exitosamente")
            return True

        except Exception as e:
            logger.error(f"Error procesando problema: {str(e)}")
            raise

    def _process_variables(self) -> None:
        """
        Procesa las variables de decisión del problema.
        Crea símbolos SymPy con propiedades real=True, positive=True.
        
        Raises:
            ValueError si variables no es diccionario
            Exception si hay error durante el procesamiento
        """
        try:
            if self.raw_problem.get("variables"):
                if not isinstance(self.raw_problem["variables"], dict):
                    raise ValueError("'variables' debe ser un diccionario")

                for var_name, description in self.raw_problem["variables"].items():
                    symbol = sp.Symbol(var_name, real=True, positive=True)
                    self.problem["variables"][symbol] = description or ""

                logger.info(f"Variables procesadas: {list(self.problem['variables'].keys())}")
        except Exception as e:
            raise Exception(f"Error procesando variables: {str(e)}")

    def _process_constraints(self) -> None:
        """
        Procesa y normaliza las restricciones del problema.
        
        Normalización:
        - Inserta multiplicaciones explícitas
        - Transforma a forma (expr, operator, rhs)
        - Para >= : convierte a -expr <= -rhs
        - Para = : mantiene como (expr, "=", rhs)
        
        Raises:
            ValueError si constraints no es lista o relación inválida
            Exception si hay error durante el procesamiento
        """
        try:
            if self.raw_problem.get("constraints"):
                if not isinstance(self.raw_problem["constraints"], list):
                    raise ValueError("'constraints' debe ser una lista")

                for constraint_str in self.raw_problem["constraints"]:
                    expr_str = insert_multiplication(constraint_str)
                    rel = sp.sympify(expr_str, locals=self.get_symbols(), evaluate=False)

                    if not isinstance(rel, Relational):
                        raise ValueError(f"Restricción inválida (no relacional): {constraint_str}")

                    lhs, rhs = rel.lhs, rel.rhs
                    
                    # Mapear operadores desde el tipo de relación
                    rel_type = type(rel).__name__
                    if "LessThan" in rel_type and "Not" not in rel_type:
                        op = "<="
                    elif "StrictLessThan" in rel_type:
                        op = "<"
                    elif "GreaterThan" in rel_type and "Not" not in rel_type:
                        op = ">="
                    elif "StrictGreaterThan" in rel_type:
                        op = ">"
                    elif "Equality" in rel_type:
                        op = "="
                    else:
                        raise ValueError(f"Tipo de relación no reconocido: {rel_type}")

                    # Normalizar según el operador
                    if op == "<=":
                        if self._is_constant(rhs):
                            self.problem["constraints"].append((lhs, "<=", float(rhs), op))  # type: ignore
                        else:
                            self.problem["constraints"].append((lhs - rhs, "<=", 0.0, op))  # type: ignore

                    elif op == ">=":
                        if self._is_constant(rhs):
                            # Verificar si es restricción de no-negatividad (lhs es variable simple, rhs == 0)
                            # Una variable simple en SymPy es de tipo Symbol
                            is_single_variable = isinstance(lhs, sp.Symbol)
                            is_zero_rhs = abs(float(rhs)) < 1e-10  # type: ignore
                            
                            if is_single_variable and is_zero_rhs:
                                # Mantener como está: (lhs, ">=", 0, ">=")
                                self.problem["constraints"].append((lhs, ">=", 0.0, op))  # type: ignore
                            else:
                                # Normalizar a <=: -lhs <= -rhs (pero guardar op original ">=")
                                self.problem["constraints"].append((-lhs, "<=", float(-rhs), op))  # type: ignore
                        else:
                            self.problem["constraints"].append((rhs - lhs, "<=", 0.0, op))  # type: ignore

                    elif op in ("==", "="):
                        if self._is_constant(rhs):
                            self.problem["constraints"].append((lhs, "=", float(rhs), op))  # type: ignore
                        else:
                            self.problem["constraints"].append((lhs - rhs, "=", 0.0, op))  # type: ignore

                    else:
                        raise ValueError(f"Operador no soportado: {op}")

                logger.info(f"Restricciones procesadas: {len(self.problem['constraints'])}")

        except Exception as e:
            raise Exception(f"Error procesando restricciones: {str(e)}")

    def _process_objective_function(self) -> None:
        """
        Procesa la función objetivo.
        
        Raises:
            ValueError si objective_function no es string
            Exception si hay error durante el procesamiento
        """
        try:
            if self.raw_problem.get("objective_function"):
                expr = self.raw_problem["objective_function"]
                if not isinstance(expr, str):
                    raise ValueError("'objective_function' debe ser un string")

                expr_str = insert_multiplication(expr)
                self.problem["objective_function"] = sp.sympify(
                    expr_str, locals=self.get_symbols(), evaluate=False
                )
                logger.info(f"Función objetivo: {self.problem['objective_function']}")

        except Exception as e:
            raise Exception(f"Error procesando función objetivo: {str(e)}")

    def _process_objective_mode(self) -> None:
        """
        Procesa el tipo de objetivo (maximización o minimización).
        Por defecto es maximización.
        
        Raises:
            ValueError si objective no es 'max' o 'min'
            Exception si hay error durante el procesamiento
        """
        try:
            if self.raw_problem.get("objective"):
                if self.raw_problem["objective"] not in ["max", "min"]:
                    raise ValueError("'objective' debe ser 'max' o 'min'")
                self.problem["objective"] = self.raw_problem["objective"]
            else:
                self.problem["objective"] = "max"

            logger.info(f"Modo objetivo: {self.problem['objective']}")

        except Exception as e:
            raise Exception(f"Error procesando modo objetivo: {str(e)}")

    @staticmethod
    def _is_constant(expr: Any) -> bool:
        """
        Verifica si una expresión SymPy es constante (sin variables).
        
        Args:
            expr: Expresión SymPy
            
        Returns:
            True si no contiene variables libres
        """
        return len(expr.free_symbols) == 0

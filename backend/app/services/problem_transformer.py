"""
Transforma problemas de programación lineal a diferentes representaciones.
Según la metodología de Hamdy A. Taha: Canonical, Standard, Matrix y Dual forms.
"""

from typing import Dict, Optional
import sympy as sp

from app.core.logger import logger
from app.services.expression_utils import clean_sympy_expression


class ProblemTransformer:
    """
    Transforma un problema normalizado a múltiples representaciones matemáticas.
    
    Representaciones soportadas:
    - Canonical: Forma original con restricciones separadas de no-negatividad
    - Standard: Max, igualdades, variables de holgura
    - Matrix: Forma matricial Ax=b, c·x
    - Dual: Problema dual según relaciones de Taha
    """

    def __init__(self, problem: Dict):
        """
        Args:
            problem: Problema normalizado desde ProblemProcessor
        """
        self.problem = problem

    def to_canonical_form(self) -> Dict:
        """
        Forma canónica (Taha, capítulos 3-4).
        
        Características:
        - Objetivo: max/min original
        - Restricciones principales: <=, >=, = (sin no-negatividad)
        - No-negatividad: separada explícitamente como x >= 0
        
        Returns:
            Dict con forma canónica
        """
        constraints = []
        non_negativity = []
        
        for expr, sign, rhs in self.problem["constraints"]:
            expr_str = clean_sympy_expression(str(expr))
            
            # Detectar condiciones de no-negatividad
            if sign in (">=", "<=") and abs(float(rhs)) < 1e-10:
                if sign == ">=":
                    non_negativity.append({
                        "expression": expr_str,
                        "operator": ">=",
                        "rhs": 0
                    })
                elif sign == "<=" and "-" in expr_str:
                    non_negativity.append({
                        "expression": expr_str.lstrip("-").strip(),
                        "operator": ">=",
                        "rhs": 0
                    })
            else:
                constraints.append({
                    "expression": expr_str,
                    "operator": sign,
                    "rhs": float(rhs) if isinstance(rhs, (int, float)) else str(rhs)
                })
        
        return {
            "form": "canonical",
            "objective": self.problem["objective"],
            "objective_function": clean_sympy_expression(str(self.problem["objective_function"])),
            "constraints": constraints,
            "non_negativity": non_negativity,
            "variables": {str(var): desc for var, desc in self.problem["variables"].items()},
        }

    def to_standard_form(self) -> Dict:
        """
        Forma estándar (Taha).
        
        Características:
        - Objetivo: Respeta el original (max o min)
        - Restricciones: IGUALDADES (agrega variables de holgura/exceso)
        - No-negatividad: separada como x >= 0
        
        Returns:
            Dict con forma estándar y variables de holgura
        """
        objective_fn = self.problem["objective_function"]
        constraints = self.problem["constraints"]
        variables = self.problem["variables"]
        standard_objective = self.problem["objective"]  # Respeta el objetivo original

        std_constraints = []
        non_negativity = []
        slack_variables = {}
        slack_idx = 1

        for expr, sign, rhs in constraints:
            expr_str = clean_sympy_expression(str(expr))
            
            # Detectar no-negatividad
            if sign in (">=", "<=") and abs(float(rhs)) < 1e-10:
                if sign == ">=":
                    non_negativity.append({
                        "expression": expr_str,
                        "operator": ">=",
                        "rhs": 0
                    })
                elif sign == "<=" and "-" in expr_str:
                    non_negativity.append({
                        "expression": expr_str.lstrip("-").strip(),
                        "operator": ">=",
                        "rhs": 0
                    })
            elif sign == "<=":
                # Agregar variable de holgura: expr + s = rhs
                slack = sp.Symbol(f"s{slack_idx}", real=True, nonnegative=True)
                slack_variables[slack] = f"Holgura {slack_idx}"
                std_constraints.append({
                    "expression": clean_sympy_expression(str(expr + slack)),
                    "operator": "=",
                    "rhs": float(rhs) if isinstance(rhs, (int, float)) else rhs
                })
                slack_idx += 1

            elif sign == "=":
                std_constraints.append({
                    "expression": clean_sympy_expression(str(expr)),
                    "operator": "=",
                    "rhs": float(rhs) if isinstance(rhs, (int, float)) else rhs
                })

            elif sign == ">=":
                # Restar variable de exceso: expr - s = rhs
                slack = sp.Symbol(f"s{slack_idx}", real=True, nonnegative=True)
                slack_variables[slack] = f"Exceso {slack_idx}"
                std_constraints.append({
                    "expression": clean_sympy_expression(str(expr - slack)),
                    "operator": "=",
                    "rhs": float(rhs) if isinstance(rhs, (int, float)) else rhs
                })
                slack_idx += 1

        return {
            "form": "standard",
            "objective": standard_objective,
            "objective_function": clean_sympy_expression(str(objective_fn)),
            "constraints": std_constraints,
            "non_negativity": non_negativity,
            "variables": {str(var): desc for var, desc in variables.items()},
            "slack_variables": {str(var): desc for var, desc in slack_variables.items()},
        }

    def to_matrix_form(self) -> Dict:
        """
        Forma matricial (Taha).
        
        Representación: max/min c·x s.a. Ax = b, x >= 0
        (respeta el objetivo original: max o min)
        
        NOTA: La matriz A contiene SOLO restricciones estructurales.
        Las condiciones de no-negatividad (x >= 0) son implícitas.
        
        Returns:
            Dict con matrices A, vector b, vector c, y objetivo original
        """
        try:
            variables_list = list(self.problem["variables"].keys())
            n_vars = len(variables_list)
            n_constraints = len(self.problem["constraints"])

            A = sp.zeros(n_constraints, n_vars)
            b = sp.Matrix([])
            c = sp.Matrix([])

            # Extraer coeficientes de restricciones
            for i, (expr, sign, rhs) in enumerate(self.problem["constraints"]):
                # Expandir la expresión para asegurar que se pueden extraer coeficientes
                expanded_expr = sp.expand(expr)
                
                for j, var in enumerate(variables_list):
                    # Extraer coeficiente, si es None significa que es 0
                    coeff = expanded_expr.coeff(var, 1)
                    if coeff is not None:
                        A[i, j] = coeff
                    else:
                        A[i, j] = 0
                
                # RHS (lado derecho) - asegurar que es float
                rhs_val = float(rhs) if isinstance(rhs, (int, float)) else rhs
                b = b.col_join(sp.Matrix([rhs_val]))

            # Extraer coeficientes de función objetivo
            expanded_obj = sp.expand(self.problem["objective_function"])
            for var in variables_list:
                coeff = expanded_obj.coeff(var, 1)
                if coeff is not None:
                    c = c.col_join(sp.Matrix([coeff]))
                else:
                    c = c.col_join(sp.Matrix([0]))

            return {
                "form": "matrix",
                "objective": self.problem["objective"],
                "A": clean_sympy_expression(str(A)),
                "b": clean_sympy_expression(str(b.T)),
                "c": clean_sympy_expression(str(c.T)),
                "variables": [str(var) for var in variables_list],
                "note": "Non-negativity conditions (x >= 0) are implicit",
                "dimensions": {
                    "constraints": n_constraints,
                    "variables": n_vars
                }
            }

        except Exception as e:
            logger.error(f"Error convertiendo a forma matricial: {str(e)}")
            return {"form": "matrix", "error": str(e)}

    def to_dual_problem(self) -> Optional[Dict]:
        """
        Genera el problema DUAL (Taha).
        
        IMPORTANTE: Solo se generan variables duales para restricciones ESTRUCTURALES.
        Las condiciones de no-negatividad del primal no generan restricciones duales.
        
        Relaciones Primal-Dual:
        - Primal max: min b·y s.a. A^T·y >= c, y >= 0
        - Primal min: max b·y s.a. A^T·y <= c, y >= 0
        
        Returns:
            Dict con problema dual, o None si no hay restricciones estructurales
        """
        try:
            variables_list = list(self.problem["variables"].keys())
            n_vars = len(variables_list)
            primal_objective = self.problem["objective"]

            # FILTRAR: Solo restricciones estructurales
            structural_constraints = []
            for expr, sign, rhs in self.problem["constraints"]:
                # Ignorar no-negatividad
                if sign in (">=", "<=") and abs(float(rhs)) < 1e-10:
                    continue
                structural_constraints.append((expr, sign, rhs))

            m = len(structural_constraints)
            if m == 0:
                logger.warning("No hay restricciones estructurales para el dual")
                return None

            # Construir matriz A con restricciones estructurales
            A = sp.zeros(m, n_vars)
            b = []
            c = []

            for i, (expr, sign, rhs) in enumerate(structural_constraints):
                # Expandir la expresión para extraer coeficientes correctamente
                expanded_expr = sp.expand(expr)
                
                for j, var in enumerate(variables_list):
                    coeff = expanded_expr.coeff(var, 1)
                    if coeff is not None:
                        A[i, j] = coeff
                    else:
                        A[i, j] = 0
                        
                b.append(float(rhs) if isinstance(rhs, (int, float)) else rhs)

            # Expandir función objetivo y extraer coeficientes
            expanded_obj = sp.expand(self.problem["objective_function"])
            for var in variables_list:
                coeff = expanded_obj.coeff(var, 1)
                c.append(float(coeff) if coeff is not None else 0)

            # Variables duales
            dual_vars = [sp.Symbol(f"y{i+1}", real=True, nonnegative=True) 
                        for i in range(m)]

            # Función objetivo dual
            dual_objective = sum(b[i] * dual_vars[i] for i in range(m))
            dual_objective_type = "min" if primal_objective == "max" else "max"

            # Restricciones duales
            A_T = A.T
            dual_constraints = []
            
            for j in range(n_vars):
                expr = sum(A_T[j, i] * dual_vars[i] for i in range(m))
                op = ">=" if primal_objective == "max" else "<="
                dual_constraints.append((expr, op, c[j]))

            non_negativity = [
                {
                    "expression": str(dual_vars[i]),
                    "operator": ">=",
                    "rhs": 0
                }
                for i in range(m)
            ]

            dual_var_names = [str(var) for var in dual_vars]

            return {
                "form": "dual",
                "objective": dual_objective_type,
                "objective_function": clean_sympy_expression(str(dual_objective)),
                "constraints": [
                    {
                        "expression": clean_sympy_expression(str(expr)),
                        "operator": op,
                        "rhs": float(rhs) if isinstance(rhs, (int, float)) else str(rhs)
                    }
                    for expr, op, rhs in dual_constraints
                ],
                "non_negativity": non_negativity,
                "variables": {var: f"Dual variable for constraint {i+1}" 
                            for i, var in enumerate(dual_var_names)},
                #"structural_constraints_count": m,
                "primal_objective": primal_objective,
                "primal_variables_count": n_vars,
                "dual_variables_count": m,
            }

        except Exception as e:
            logger.error(f"Error generando problema dual: {str(e)}")
            return None

    def get_all_representations(self) -> Dict:
        """
        Genera todas las representaciones del problema.
        
        Returns:
            Dict con formas: canonical, standard, matrix, dual
        """
        return {
            "canonical": self.to_canonical_form(),
            "standard": self.to_standard_form(),
            "matrix": self.to_matrix_form(),
            "dual": self.to_dual_problem(),
        }

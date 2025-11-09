"""
Transforma problemas de programación lineal a diferentes representaciones.
Según la metodología de Hamdy A. Taha: Canonical, Standard, Matrix y Dual forms.
"""

from typing import Dict, Optional
import sympy as sp

from app.core.logger import logger
from app.services.expression_utils import clean_sympy_expression, reorder_expression_terms, matrix_to_nested_list


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

    def _unpack_constraint(self, constraint_data):
        """
        Helper para desempacar restricciones que pueden tener 3 o 4 elementos.
        
        Returns:
            Tupla (expr, sign, rhs, original_op)
        """
        if len(constraint_data) == 4:
            expr, sign, rhs, original_op = constraint_data
        else:
            expr, sign, rhs = constraint_data
            original_op = sign
        return expr, sign, rhs, original_op

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
        
        for constraint_data in self.problem["constraints"]:
            expr, sign, rhs, _ = self._unpack_constraint(constraint_data)
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
            "recommended_for": "Teoría y análisis inicial del problema. Mantiene la forma natural sin modificaciones."
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

        for constraint_data in constraints:
            expr, sign, rhs, _ = self._unpack_constraint(constraint_data)
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
                combined_expr = expr + slack
                expr_cleaned = clean_sympy_expression(str(combined_expr))
                # Reordenar: variables originales primero, luego holgura
                original_var_names = [str(v) for v in variables.keys()]
                slack_var_names = [f"s{j+1}" for j in range(slack_idx)]
                expr_reordered = reorder_expression_terms(expr_cleaned, original_var_names, slack_var_names)
                std_constraints.append({
                    "expression": expr_reordered,
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
                combined_expr = expr - slack
                expr_cleaned = clean_sympy_expression(str(combined_expr))
                # Reordenar: variables originales primero, luego exceso
                original_var_names = [str(v) for v in variables.keys()]
                slack_var_names = [f"s{j+1}" for j in range(slack_idx)]
                expr_reordered = reorder_expression_terms(expr_cleaned, original_var_names, slack_var_names)
                std_constraints.append({
                    "expression": expr_reordered,
                    "operator": "=",
                    "rhs": float(rhs) if isinstance(rhs, (int, float)) else rhs
                })
                slack_idx += 1

        # Agregar no-negatividad de variables originales (si no estaban explícitas)
        for var, desc in variables.items():
            var_str = str(var)
            # Verificar si ya existe esta variable en no_negativity
            already_exists = any(var_str in expr.get("expression", "") for expr in non_negativity)
            if not already_exists:
                non_negativity.append({
                    "expression": var_str,
                    "operator": ">=",
                    "rhs": 0
                })
        
        # Agregar no-negatividad de variables de holgura/exceso
        for slack_var in slack_variables.keys():
            non_negativity.append({
                "expression": str(slack_var),
                "operator": ">=",
                "rhs": 0
            })

        return {
            "form": "standard",
            "objective": standard_objective,
            "objective_function": clean_sympy_expression(str(objective_fn)),
            "constraints": std_constraints,
            "non_negativity": non_negativity,
            "variables": {str(var): desc for var, desc in variables.items()},
            "slack_variables": {str(var): desc for var, desc in slack_variables.items()},
            "recommended_for": "Algoritmo Simplex, ya que todas las restricciones son igualdades con variables de holgura/exceso."
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
            
            # FILTRAR: Solo restricciones estructurales (excluir no-negatividad donde rhs ≈ 0)
            structural_constraints = []
            for constraint_data in self.problem["constraints"]:
                expr, sign, rhs, _ = self._unpack_constraint(constraint_data)
                
                # Ignorar restricciones de no-negatividad (rhs ≈ 0)
                if not (sign in (">=", "<=") and abs(float(rhs)) < 1e-10):
                    structural_constraints.append((expr, sign, rhs))
            
            n_constraints = len(structural_constraints)
            
            A = sp.zeros(n_constraints, n_vars)
            b = sp.Matrix([])
            c = sp.Matrix([])

            # Extraer coeficientes de restricciones estructurales SOLO
            for i, (expr, sign, rhs) in enumerate(structural_constraints):
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
                "A": matrix_to_nested_list(clean_sympy_expression(str(A))),
                "b": matrix_to_nested_list(clean_sympy_expression(str(b.T))),
                "c": matrix_to_nested_list(clean_sympy_expression(str(c.T))),
                "variables": [str(var) for var in variables_list],
                "note": "Non-negativity conditions (x >= 0) are implicit",
                "dimensions": {
                    "constraints": n_constraints,
                    "variables": n_vars
                },
                "recommended_for": "Análisis algebraico y cálculos de operaciones matriciales. Forma compacta para problemas grandes."
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
            for constraint_data in self.problem["constraints"]:
                expr, sign, rhs, _ = self._unpack_constraint(constraint_data)
                
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
                # Construir la suma: suma_i (A_T[j, i] * y_i)
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
                "primal_objective": primal_objective,
                "primal_variables_count": n_vars,
                "dual_variables_count": m,
                "recommended_for": "Análisis de sensibilidad, precios sombra y verificación de optimalidad mediante dualidad fuerte (Teorema de holgura complementaria)."
            }

        except Exception as e:
            logger.error(f"Error generando problema dual: {str(e)}")
            return None

    def to_big_m_form(self) -> Optional[Dict]:
        """
        Método de la Gran M (Big M Method).
        
        Características:
        - Agrega variables artificiales para restricciones >= e =
        - Penaliza variables artificiales con -M (maximización) o +M (minimización)
        - M es una constante suficientemente grande (típicamente 10^6)
        - Variables de holgura para restricciones <=
        - Variables de exceso (negativo de holgura) para restricciones >=
        
        Proceso:
        1. Para cada restricción >=: agrega variable de exceso negativa
        2. Para cada restricción = o >=: agrega variable artificial
        3. Modifica objetivo para penalizar artificiales
        
        Returns:
            Dict con forma Big M o None si hay error
        """
        try:
            M = sp.Symbol('M', positive=True, real=True)
            objective_type = self.problem["objective"]
            original_objective = self.problem["objective_function"]
            
            slack_count = 0
            artificial_count = 0
            slack_vars = {}
            artificial_vars = {}
            
            big_m_constraints = []
            symbols_dict = {}
            
            # Recopilar todas las variables originales
            for var_name in self.problem["variables"].keys():
                symbols_dict[str(var_name)] = var_name
            
            # Procesar restricciones
            for constraint_data in self.problem["constraints"]:
                expr, sign, rhs, original_op = self._unpack_constraint(constraint_data)
                
                # Ignorar restricciones de no-negatividad (rhs ≈ 0)
                if sign in (">=", "<=") and abs(float(rhs)) < 1e-10:
                    continue
                
                # Si la restricción fue normalizada (original_op != sign), invertir
                if original_op == ">=" and sign == "<=":
                    # La restricción fue invertida: -expr <= -rhs
                    # Necesitamos volver a: expr >= rhs
                    expr = -expr
                    rhs = -rhs
                
                expr_str = clean_sympy_expression(str(expr))
                expr_sympy = sp.sympify(expr_str, locals=symbols_dict, evaluate=False)
                
                # Usar el operador ORIGINAL para determinar qué variable agregar
                if original_op == "<=":
                    # Restricción <=: agregar variable de holgura positiva
                    slack_count += 1
                    slack_var_name = f"s{slack_count}"
                    slack_vars[slack_var_name] = f"Holgura {slack_count}"
                    new_expr = f"{expr_str} + {slack_var_name}"
                    
                elif original_op == ">=":
                    # Restricción >=: agregar variable de exceso (negativa) + variable artificial
                    slack_count += 1
                    artificial_count += 1
                    slack_var_name = f"e{slack_count}"
                    artificial_var_name = f"A{artificial_count}"
                    slack_vars[slack_var_name] = f"Variable de exceso {slack_count}"
                    artificial_vars[artificial_var_name] = f"Variable artificial {artificial_count}"
                    new_expr = f"{expr_str} - {slack_var_name} + {artificial_var_name}"
                    
                elif original_op == "=":
                    # Restricción =: solo agregar variable artificial
                    artificial_count += 1
                    artificial_var_name = f"A{artificial_count}"
                    artificial_vars[artificial_var_name] = f"Variable artificial {artificial_count}"
                    new_expr = f"{expr_str} + {artificial_var_name}"
                
                big_m_constraints.append({
                    "expression": new_expr,
                    "operator": "=",
                    "rhs": float(rhs) if isinstance(rhs, (int, float)) else str(rhs)
                })
            
            # Modificar función objetivo para penalizar variables artificiales
            objective_str = clean_sympy_expression(str(original_objective))
            
            if artificial_vars:
                # Agregar penalidad -M para cada variable artificial
                penalty_terms = " - M*" + " - M*".join(artificial_vars.keys())
                if objective_type == "max":
                    new_objective = f"{objective_str}{penalty_terms}"
                else:  # min
                    # Para minimización: +M*artificial_vars
                    penalty_terms = " + M*" + " + M*".join(artificial_vars.keys())
                    new_objective = f"{objective_str}{penalty_terms}"
            else:
                new_objective = objective_str
            
            # Agregar no-negatividad para todas las variables
            non_negativity = []
            
            # Variables originales
            for var_name in self.problem["variables"].keys():
                non_negativity.append({
                    "expression": str(var_name),
                    "operator": ">=",
                    "rhs": 0
                })
            
            # Variables de holgura y exceso
            for slack_var in slack_vars.keys():
                non_negativity.append({
                    "expression": slack_var,
                    "operator": ">=",
                    "rhs": 0
                })
            
            # Variables artificiales
            for artificial_var in artificial_vars.keys():
                non_negativity.append({
                    "expression": artificial_var,
                    "operator": ">=",
                    "rhs": 0
                })
            
            result = {
                "form": "big_m",
                "objective": objective_type,
                "objective_function": new_objective,
                "constraints": big_m_constraints,
                "non_negativity": non_negativity,
                "variables": {str(var): desc for var, desc in self.problem["variables"].items()},
            }
            
            if slack_vars:
                result["slack_variables"] = slack_vars
            
            if artificial_vars:
                result["artificial_variables"] = artificial_vars
                result["recommended_for"] = "Resolver problemas con restricciones >= o = usando Simplex. Requiere dos fases o penalización con M."
            else:
                result["recommended_for"] = "NO RECOMENDADO: Este problema no tiene restricciones >= ni =, por lo que no necesita variables artificiales. Usa Forma Estándar en su lugar."
            
            result["M"] = "Constante grande usada para penalizar las variables artificiales (típicamente 10^6)"
            result["description"] = "Método de la Gran M para problemas con restricciones >= o ="
            
            logger.info(f"Forma Big M generada: {len(slack_vars)} variables de holgura/exceso, {len(artificial_vars)} variables artificiales")
            return result
            
        except Exception as e:
            logger.error(f"Error generando forma Big M: {str(e)}")
            return None

    def get_all_representations(self) -> Dict:
        """
        Genera todas las representaciones del problema.
        
        Returns:
            Dict con formas: canonical, standard, matrix, dual, big_m
        """
        return {
            "canonical": self.to_canonical_form(),
            "standard": self.to_standard_form(),
            "matrix": self.to_matrix_form(),
            "dual": self.to_dual_problem(),
            "big_m": self.to_big_m_form(),
        }

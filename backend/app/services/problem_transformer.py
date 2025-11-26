"""
Transforma problemas de programación lineal a diferentes representaciones.
Según la metodología de Hamdy A. Taha: Canonical, Standard, Matrix y Dual forms.
"""

from typing import Dict, Optional, List, Tuple, Any
import sympy as sp

from app.core.logger import logger
from app.services.expression_utils import clean_sympy_expression, reorder_expression_terms, matrix_to_nested_list


class ProblemTransformer:
    """Transforma problemas a múltiples representaciones matemáticas (Taha methodology)."""

    _NONNEG_TOL = 1e-10

    def __init__(self, problem: Dict):
        """Args: problem: Problema normalizado desde ProblemProcessor"""
        self.problem = problem

    def _unpack_constraint(self, constraint_data: Tuple) -> Tuple:
        """Desempaca restricciones que pueden tener 3 o 4 elementos."""
        return constraint_data if len(constraint_data) == 4 else \
               (*constraint_data, constraint_data[1])

    def _is_nonnegative_constraint(self, constraint_data: Tuple) -> bool:
        """Verifica si una restricción es de no-negatividad (x >= 0 o x <= 0)."""
        expr, sign, rhs, _ = self._unpack_constraint(constraint_data)
        return sign in (">=", "<=") and abs(float(rhs)) < self._NONNEG_TOL

    def _filter_structural_constraints(self) -> List[Tuple]:
        """Extrae solo restricciones estructurales (excluye no-negatividad)."""
        return [(sp.expand(expr), sign, rhs) 
                for constraint_data in self.problem["constraints"]
                if not self._is_nonnegative_constraint(constraint_data)
                for expr, sign, rhs, _ in [self._unpack_constraint(constraint_data)]]

    def _extract_nonnegative_constraints(self) -> List[Dict]:
        """Extrae restricciones de no-negatividad del problema."""
        non_neg = []
        for constraint_data in self.problem["constraints"]:
            if not self._is_nonnegative_constraint(constraint_data):
                continue
            expr, sign, rhs, _ = self._unpack_constraint(constraint_data)
            expr_str = clean_sympy_expression(str(expr))
            if sign == ">=" or (sign == "<=" and "-" in expr_str):
                non_neg.append({
                    "expression": expr_str.lstrip("-").strip() if sign == "<=" else expr_str,
                    "operator": ">=",
                    "rhs": 0
                })
        return non_neg

    def _build_constraint_dict(self, expr: sp.Expr, sign: str, rhs: float) -> Dict:
        """Construye dict de restricción normalizado."""
        return {
            "expression": clean_sympy_expression(str(expr)),
            "operator": sign,
            "rhs": float(rhs) if isinstance(rhs, (int, float)) else str(rhs)
        }

    def _create_slack_or_excess(self, idx: int, is_slack: bool = True) -> Tuple[sp.Symbol, str]:
        """Crea variable de holgura o exceso."""
        prefix = "s" if is_slack else "e"
        var = sp.Symbol(f"{prefix}{idx}", real=True, nonnegative=True)
        desc = f"Holgura {idx}" if is_slack else f"Exceso {idx}"
        return var, desc

    def _extract_matrix_coefficients(self, constraints: List[Tuple], 
                                     variables_list: List) -> Tuple[sp.Matrix, sp.Matrix]:
        """Extrae coeficientes de restricciones en forma matricial."""
        m, n = len(constraints), len(variables_list)
        A = sp.zeros(m, n)
        b = sp.Matrix([])
        
        for i, (expr, sign, rhs) in enumerate(constraints):
            expanded = sp.expand(expr)
            for j, var in enumerate(variables_list):
                A[i, j] = expanded.coeff(var, 1) or 0
            b = b.col_join(sp.Matrix([float(rhs) if isinstance(rhs, (int, float)) else rhs]))
        
        return A, b

    def _extract_objective_coefficients(self, variables_list: List) -> sp.Matrix:
        """Extrae coeficientes de la función objetivo."""
        expanded = sp.expand(self.problem["objective_function"])
        return sp.Matrix([expanded.coeff(var, 1) or 0 for var in variables_list])

    def _build_nonnegative_list(self, var_dict: Dict, slack_dict: Dict = None) -> List[Dict]:
        """Construye lista de condiciones de no-negatividad."""
        non_neg = [{"expression": str(var), "operator": ">=", "rhs": 0} for var in var_dict.keys()]
        if slack_dict:
            non_neg.extend([{"expression": str(var), "operator": ">=", "rhs": 0} for var in slack_dict.keys()])
        return non_neg

    def _sanitize_for_serialization(self, obj: Any) -> Any:
        """Convierte objetos SymPy no serializables a strings."""
        if isinstance(obj, dict):
            return {str(k) if isinstance(k, sp.Symbol) else k: 
                    self._sanitize_for_serialization(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_serialization(item) for item in obj]
        elif isinstance(obj, sp.Symbol):
            return str(obj)
        return obj

    def to_canonical_form(self) -> Dict:
        """Forma canónica (Taha). Max/Min original, restricciones <=/>=/=."""
        constraints = [self._build_constraint_dict(expr, sign, rhs)
                      for constraint_data in self.problem["constraints"]
                      if not self._is_nonnegative_constraint(constraint_data)
                      for expr, sign, rhs, _ in [self._unpack_constraint(constraint_data)]]
        
        return {
            "form": "canonical",
            "objective": self.problem["objective"],
            "objective_function": clean_sympy_expression(str(self.problem["objective_function"])),
            "constraints": constraints,
            "non_negativity": self._extract_nonnegative_constraints(),
            "variables": {str(var): desc for var, desc in self.problem["variables"].items()},
            "recommended_for": "Teoría y análisis inicial del problema. Mantiene la forma natural sin modificaciones."
        }

    def to_standard_form(self) -> Dict:
        """Forma estándar (Taha). Max/Min original, igualdades, variables de holgura/exceso."""
        constraints, slack_vars, slack_idx = [], {}, 1
        
        for constraint_data in self.problem["constraints"]:
            if self._is_nonnegative_constraint(constraint_data):
                continue
            
            expr, sign, rhs, _ = self._unpack_constraint(constraint_data)
            original_vars = [str(v) for v in self.problem["variables"].keys()]
            slack_var_names = [f"s{j+1}" for j in range(slack_idx)]
            
            if sign == "<=":
                slack, desc = self._create_slack_or_excess(slack_idx)
                slack_vars[slack] = desc
                combined = expr + slack
                expr_reordered = reorder_expression_terms(
                    clean_sympy_expression(str(combined)), original_vars, slack_var_names)
                constraints.append(self._build_constraint_dict(expr_reordered, "=", rhs))
                slack_idx += 1
            elif sign == "=":
                constraints.append(self._build_constraint_dict(expr, "=", rhs))
            elif sign == ">=":
                slack, desc = self._create_slack_or_excess(slack_idx, False)
                slack_vars[slack] = desc
                combined = expr - slack
                expr_reordered = reorder_expression_terms(
                    clean_sympy_expression(str(combined)), original_vars, slack_var_names)
                constraints.append(self._build_constraint_dict(expr_reordered, "=", rhs))
                slack_idx += 1
        
        return {
            "form": "standard",
            "objective": self.problem["objective"],
            "objective_function": clean_sympy_expression(str(self.problem["objective_function"])),
            "constraints": constraints,
            "non_negativity": self._build_nonnegative_list(self.problem["variables"], slack_vars),
            "variables": {str(var): desc for var, desc in self.problem["variables"].items()},
            "slack_variables": {str(var): desc for var, desc in slack_vars.items()},
            "recommended_for": "Algoritmo Simplex, ya que todas las restricciones son igualdades con variables de holgura/exceso."
        }

    def to_matrix_form(self) -> Dict:
        """Forma matricial (Taha). Representación: max/min c·x s.a. Ax = b, x >= 0."""
        try:
            variables_list = list(self.problem["variables"].keys())
            structural_constraints = self._filter_structural_constraints()
            
            A, b = self._extract_matrix_coefficients(structural_constraints, variables_list)
            c = self._extract_objective_coefficients(variables_list)
            
            return {
                "form": "matrix",
                "objective": self.problem["objective"],
                "A": matrix_to_nested_list(clean_sympy_expression(str(A))),
                "b": matrix_to_nested_list(clean_sympy_expression(str(b.T))),
                "c": matrix_to_nested_list(clean_sympy_expression(str(c.T))),
                "variables": [str(var) for var in variables_list],
                "note": "Non-negativity conditions (x >= 0) are implicit",
                "dimensions": {
                    "constraints": len(structural_constraints),
                    "variables": len(variables_list)
                },
                "recommended_for": "Análisis algebraico y cálculos de operaciones matriciales. Forma compacta para problemas grandes."
            }
        except Exception as e:
            logger.error(f"Error convertiendo a forma matricial: {str(e)}")
            return {"form": "matrix", "error": str(e)}

    def to_dual_problem(self) -> Optional[Dict]:
        """Genera el problema DUAL (Taha). Variables duales solo para restricciones estructurales."""
        try:
            variables_list = list(self.problem["variables"].keys())
            structural_constraints = self._filter_structural_constraints()
            m = len(structural_constraints)
            
            if m == 0:
                logger.warning("No hay restricciones estructurales para el dual")
                return None
            
            A, b_matrix = self._extract_matrix_coefficients(structural_constraints, variables_list)
            c_vec = self._extract_objective_coefficients(variables_list)
            
            b = [float(b_matrix[i, 0]) for i in range(m)]
            c = [float(c_vec[i, 0]) for i in range(len(variables_list))]
            
            dual_vars = [sp.Symbol(f"y{i+1}", real=True, nonnegative=True) for i in range(m)]
            dual_objective = sum(b[i] * dual_vars[i] for i in range(m))
            dual_objective_type = "min" if self.problem["objective"] == "max" else "max"
            
            A_T = A.T
            dual_constraints = [self._build_constraint_dict(
                sum(A_T[j, i] * dual_vars[i] for i in range(m)),
                ">=" if self.problem["objective"] == "max" else "<=",
                c[j]
            ) for j in range(len(variables_list))]
            
            dual_var_names = [str(var) for var in dual_vars]
            
            return {
                "form": "dual",
                "objective": dual_objective_type,
                "objective_function": clean_sympy_expression(str(dual_objective)),
                "constraints": dual_constraints,
                "non_negativity": [{"expression": str(dual_vars[i]), "operator": ">=", "rhs": 0} 
                                  for i in range(m)],
                "variables": {var: f"Dual variable for constraint {i+1}" 
                            for i, var in enumerate(dual_var_names)},
                "primal_objective": self.problem["objective"],
                "primal_variables_count": len(variables_list),
                "dual_variables_count": m,
                "recommended_for": "Análisis de sensibilidad, precios sombra y verificación de optimalidad mediante dualidad fuerte."
            }
        except Exception as e:
            logger.error(f"Error generando problema dual: {str(e)}")
            return None

    def to_big_m_form(self) -> Optional[Dict]:
        """Método de la Gran M. Penaliza variables artificiales con -M (max) o +M (min)."""
        try:
            objective_type = self.problem["objective"]
            original_objective = self.problem["objective_function"]
            slack_count = artificial_count = 0
            slack_vars, artificial_vars = {}, {}
            big_m_constraints = []
            symbols_dict = {str(var): var for var in self.problem["variables"].keys()}
            
            for constraint_data in self.problem["constraints"]:
                if self._is_nonnegative_constraint(constraint_data):
                    continue
                
                expr, sign, rhs, original_op = self._unpack_constraint(constraint_data)
                if original_op == ">=" and sign == "<=":
                    expr, rhs = -expr, -rhs
                
                expr_str = clean_sympy_expression(str(expr))
                
                if original_op == "<=":
                    slack_count += 1
                    slack_vars[f"s{slack_count}"] = f"Holgura {slack_count}"
                    new_expr = f"{expr_str} + s{slack_count}"
                elif original_op == ">=":
                    slack_count += 1
                    artificial_count += 1
                    slack_vars[f"e{slack_count}"] = f"Variable de exceso {slack_count}"
                    artificial_vars[f"A{artificial_count}"] = f"Variable artificial {artificial_count}"
                    new_expr = f"{expr_str} - e{slack_count} + A{artificial_count}"
                elif original_op == "=":
                    artificial_count += 1
                    artificial_vars[f"A{artificial_count}"] = f"Variable artificial {artificial_count}"
                    new_expr = f"{expr_str} + A{artificial_count}"
                
                big_m_constraints.append(self._build_constraint_dict(new_expr, "=", rhs))
            
            objective_str = clean_sympy_expression(str(original_objective))
            if artificial_vars:
                penalty = " - M*" + " - M*".join(artificial_vars.keys())
                new_objective = f"{objective_str}{penalty}" if objective_type == "max" else \
                               f"{objective_str} + M*" + " + M*".join(artificial_vars.keys())
            else:
                new_objective = objective_str
            
            non_neg = []
            for var_name in self.problem["variables"].keys():
                non_neg.append({"expression": str(var_name), "operator": ">=", "rhs": 0})
            for slack_var in slack_vars.keys():
                non_neg.append({"expression": slack_var, "operator": ">=", "rhs": 0})
            for artificial_var in artificial_vars.keys():
                non_neg.append({"expression": artificial_var, "operator": ">=", "rhs": 0})
            
            result = {
                "form": "big_m",
                "objective": objective_type,
                "objective_function": new_objective,
                "constraints": big_m_constraints,
                "non_negativity": non_neg,
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
        """Genera todas las representaciones del problema."""
        representations = {
            "canonical": self.to_canonical_form(),
            "standard": self.to_standard_form(),
            "matrix": self.to_matrix_form(),
            "dual": self.to_dual_problem(),
            "big_m": self.to_big_m_form(),
        }
        
        return self._sanitize_for_serialization(representations)

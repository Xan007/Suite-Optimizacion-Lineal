"""
SolverService: Implementación didáctica del método Simplex con visualización de tablas.
"""

from typing import Dict, List, Optional, Tuple, Any
import sympy as sp
import numpy as np

from app.schemas.analyze_schema import MathematicalModel
from app.core.logger import logger
from app.services.graphication_service import GraphicationService
from app.services.big_m_method import BigMMethod

try:
    import pulp
except Exception:
    pulp = None


class SolverService:
    """Servicio para resolver problemas de optimización lineal con Simplex didáctico."""

    _TOL = 1e-10
    _FEASIBLE_TOL = 1e-6

    def __init__(self):
        pass

    def _safe_float_conversion(self, expr: Any) -> float:
        """Convierte expresión SymPy a float de forma segura."""
        try:
            if expr is None or expr == 0:
                return 0.0
            # Si es un número, convertir directamente
            if isinstance(expr, (int, float)):
                return float(expr)
            # Si es SymPy, evaluar numéricamente
            if isinstance(expr, sp.Basic):
                return float(expr.evalf())
            return float(expr)
        except Exception as e:
            logger.warning(f"Error convirtiendo {expr} a float: {e}, retornando 0.0")
            return 0.0

    def determine_applicable_methods(self, model: MathematicalModel) -> Tuple[List[str], Dict[str, str]]:
        """Retorna métodos sugeridos y no aplicables."""
        # Detectar si el problema necesita el método de la Gran M
        needs_big_m = self._needs_big_m(model)
        
        suggested = ["simplex"]
        if needs_big_m:
            suggested.insert(0, "big_m")
        
        not_applicable = {"graphical": "Más de 2 variables"} if len(model.variables) > 2 else {}
        if len(model.variables) <= 2:
            suggested.append("graphical")
        return suggested, not_applicable

    def _needs_big_m(self, model: MathematicalModel) -> bool:
        """Verifica si el problema tiene restricciones >= o = que requieren Gran M."""
        if not model.constraints:
            return False
        
        for constraint in model.constraints:
            # Filtrar restricciones de no-negatividad
            if any(f"{v} >= 0" in constraint or f"{v} <= 0" in constraint 
                   for v in model.variables.keys()):
                continue
            
            if ">=" in constraint or "=" in constraint:
                return True
        
        return False

    def solve(self, model: MathematicalModel, method: str = "simplex") -> Dict[str, Any]:
        """Resuelve usando Simplex tableau o Gran M según el método."""
        try:
            if method == "big_m":
                return self._solve_big_m(model)
            elif method == "simplex":
                return self._simplex_tableau(model)
            elif method == "graphical":
                return self._graphical_method(model)
            else:
                return {"success": False, "error": f"Método no soportado: {method}"}
        except Exception as e:
            logger.error(f"Error en solve: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _solve_big_m(self, model: MathematicalModel) -> Dict[str, Any]:
        """Resuelve usando el método de la Gran M."""
        try:
            big_m_solver = BigMMethod()
            result = big_m_solver.solve(model)
            return self._convert_numpy_types(result)
        except Exception as e:
            logger.error(f"Error en _solve_big_m: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _interpret_big_m_solution(self, model: MathematicalModel, result: Dict[str, Any]) -> str:
        """Genera interpretación de la solución obtenida con Gran M."""
        interpretation = "**Solución por el Método de la Gran M:**\n\n"
        
        if not result.get("success"):
            return interpretation + f"Estado: {result.get('status', 'Desconocido')}"
        
        interpretation += f"**Valor Óptimo:** {result.get('objective_value', 0):.4g}\n\n"
        
        interpretation += "**Solución Óptima:**\n"
        variables = result.get("variables", {})
        for var, value in variables.items():
            interpretation += f"- {var} = {value:.4g}\n"
        
        interpretation += f"\n**Iteraciones:** {result.get('iterations', 0)}\n"
        interpretation += f"**Variables Artificiales Usadas:** {len(result.get('artificial_variables', []))}\n"
        interpretation += f"**Variables de Holgura:** {len(result.get('slack_variables', []))}\n"
        interpretation += f"**Variables de Exceso:** {len(result.get('excess_variables', []))}\n"
        
        return interpretation

    def _convert_numpy_types(self, obj: Any) -> Any:
        """Convierte tipos NumPy a tipos nativas de Python para JSON serialización."""
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj) if isinstance(obj, np.floating) else int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        return obj

    def _extract_relation_type(self, rel: Any) -> str:
        """Extrae el operador de una relación SymPy."""
        rel_type = str(type(rel).__name__)
        if "LessThan" in rel_type:
            return "<="
        elif "GreaterThan" in rel_type:
            return ">="
        elif "Equality" in rel_type:
            return "="
        return "<="

    def _parse_constraint(self, constraint_str: str, symbols: Dict[str, Any]) -> Optional[Tuple[Any, str, Any]]:
        """Parsea una restricción string a (lhs, op, rhs). Retorna None si falla."""
        try:
            rel = sp.sympify(constraint_str, locals=symbols, evaluate=False)
            if hasattr(rel, 'lhs') and hasattr(rel, 'rhs'):
                return (sp.expand(rel.lhs), self._extract_relation_type(rel), rel.rhs)
        except:
            pass
        return None

    def _filter_nonneg_constraints(self, constraints: List[str], var_names: List[str]) -> List[str]:
        """Filtra restricciones de no-negatividad."""
        return [c for c in constraints if not any(f"{v} >= 0" in c or f"{v}<= 0" in c for v in var_names)]

    def _generate_equations_latex(self, structural_constraints: List[str], var_names: List[str], 
                                  symbols: Dict[str, Any], A: np.ndarray, b: np.ndarray) -> str:
        """Genera ecuaciones LaTeX con variables de holgura para cada restricción."""
        equations = []
        for i in range(len(b)):
            var_terms = []
            for j, var in enumerate(var_names):
                coeff = float(A[i, j])
                if abs(coeff) > self._TOL:
                    coeff_str = f"{int(coeff)}" if coeff == int(coeff) else f"{coeff:.4g}"
                    base_name = var.rstrip('0123456789')
                    var_idx = j + 1
                    var_sub = f"{base_name}_{{{var_idx}}}"
                    if coeff == 1:
                        var_terms.append(f"{var_sub}")
                    elif coeff == -1:
                        var_terms.append(f"-{var_sub}")
                    elif coeff > 0:
                        var_terms.append(f"{coeff_str}{var_sub}")
                    else:
                        var_terms.append(f"{coeff_str}{var_sub}")
            
            eq = var_terms[0] if var_terms else "0"
            for term in var_terms[1:]:
                eq += f" + {term}" if not term.startswith("-") else f" {term}"
            
            slack_name = f"s_{{{i+1}}}"
            rhs = float(b[i])
            
            latex_eq = f"{eq} + {slack_name} = {int(rhs) if rhs == int(rhs) else f'{rhs:.4g}'}"
            equations.append(f"\\[{latex_eq}\\]")
        
        return "\n".join(equations)

    def _generate_equations_latex_graphical(self, structural_constraints: List[str], var_names: List[str],
                                           symbols: Dict[str, Any], A: np.ndarray, b: np.ndarray) -> str:
        """Genera ecuaciones LaTeX con variables de holgura para método gráfico."""
        equations = []
        for i in range(len(b)):
            var_terms = []
            for j, var in enumerate(var_names):
                coeff = float(A[i, j])
                if abs(coeff) > self._TOL:
                    coeff_str = f"{int(coeff)}" if coeff == int(coeff) else f"{coeff:.4g}"
                    base_name = var.rstrip('0123456789')
                    var_idx = j + 1
                    var_sub = f"{base_name}_{{{var_idx}}}"
                    if coeff == 1:
                        var_terms.append(f"{var_sub}")
                    elif coeff == -1:
                        var_terms.append(f"-{var_sub}")
                    elif coeff > 0:
                        var_terms.append(f"{coeff_str}{var_sub}")
                    else:
                        var_terms.append(f"{coeff_str}{var_sub}")
            
            eq = var_terms[0] if var_terms else "0"
            for term in var_terms[1:]:
                eq += f" + {term}" if not term.startswith("-") else f" {term}"
            
            slack_name = f"s_{{{i+1}}}"
            rhs = float(b[i])
            
            latex_eq = f"{eq} + {slack_name} = {int(rhs) if rhs == int(rhs) else f'{rhs:.4g}'}"
            equations.append(f"\\[{latex_eq}\\]")
        
        return "\n".join(equations)

    def _simplex_tableau(self, model: MathematicalModel) -> Dict[str, Any]:
        """Método Simplex Tableau con tablas en cada iteración."""
        try:
            var_names = list(model.variables.keys())
            n = len(var_names)
            symbols = {name: sp.Symbol(name, real=True, positive=True) for name in var_names}
            
            # Parsear función objetivo
            obj_expr = sp.sympify(model.objective_function, locals=symbols)
            c = np.array([self._safe_float_conversion(obj_expr.coeff(symbols[v], 1) or 0) for v in var_names])
            is_max = model.objective == "max"
            if not is_max:
                c = -c
            
            # Parsear restricciones
            structural_constraints = self._filter_nonneg_constraints(model.constraints or [], var_names)
            A, b = [], []
            
            for constraint_str in structural_constraints:
                parsed = self._parse_constraint(constraint_str, symbols)
                if not parsed:
                    continue
                lhs, op, rhs_val = parsed
                row = np.array([self._safe_float_conversion(lhs.coeff(symbols[v], 1) or 0) for v in var_names])
                if '>=' in op:
                    row, rhs_val = -row, -self._safe_float_conversion(rhs_val)
                A.append(row)
                b.append(self._safe_float_conversion(rhs_val))
            
            if not A:
                return {"success": False, "error": "No hay restricciones estructurales", "steps": []}
            
            A, b, m = np.array(A), np.array(b), len(b)
            tableau = np.hstack([A, np.eye(m), b.reshape(-1, 1)])
            obj_row = np.hstack([[-ci for ci in c], np.zeros(m), [0]])
            basis = [f"s{i+1}" for i in range(m)]
            basis_cols = list(range(n, n + m))
            
            steps = []
            for _ in range(100):
                entering_col = np.argmin(obj_row[:-1])
                if obj_row[entering_col] >= -self._TOL:
                    break
                
                ratios = [tableau[i, -1] / tableau[i, entering_col] if tableau[i, entering_col] > self._TOL else float('inf') 
                          for i in range(m)]
                leaving_row = np.argmin(ratios)
                
                if ratios[leaving_row] == float('inf'):
                    return {"success": False, "error": "Problema ilimitado", "steps": []}
                
                tableau_before, obj_row_before, basis_before = tableau.copy(), obj_row.copy(), basis[:]
                pivot = tableau[leaving_row, entering_col]
                tableau[leaving_row] /= pivot
                for i in range(m):
                    if i != leaving_row:
                        tableau[i] -= tableau[i, entering_col] * tableau[leaving_row]
                obj_row = obj_row - obj_row[entering_col] * np.hstack([tableau[leaving_row]])
                
                entering_name = var_names[entering_col] if entering_col < n else f"s{entering_col - n + 1}"
                leaving_name = basis[leaving_row]
                basis[leaving_row], basis_cols[leaving_row] = entering_name, entering_col
                
                steps.append({
                    "iteration": len(steps) + 1,
                    "type": "iteration",
                    "description": f"Entra {entering_name}, Sale {leaving_name}",
                    "entering_variable": entering_name,
                    "leaving_variable": leaving_name,
                    "pivot_row": int(leaving_row),
                    "leaving_row": int(leaving_row),
                    "entering_col": int(entering_col),
                    "pivot_column": int(entering_col),
                    "pivot_element": float(pivot),
                    "tableau_before": tableau_before.tolist(),
                    "obj_row_before": obj_row_before.tolist(),
                    "basis_before": basis_before,
                    "tableau_after": tableau.copy().tolist(),
                    "obj_row_after": obj_row.copy().tolist(),
                    "basis_after": basis[:],
                    "var_names": var_names,
                    "slack_names": [f"s{i+1}" for i in range(m)]
                })
            
            solution = {v: self._safe_float_conversion(tableau[[i for i, bv in enumerate(basis) if bv == v][0], -1]) if v in basis else 0.0 
                       for v in var_names}
            obj_value = self._safe_float_conversion(obj_row[-1]) if is_max else -self._safe_float_conversion(obj_row[-1])
            
            # Generar ecuaciones LaTeX con variables de holgura
            equations_latex = self._generate_equations_latex(structural_constraints, var_names, symbols, A, b)
            
            return self._convert_numpy_types({
                "success": True,
                "method": "simplex",
                "status": "optimal",
                "objective_value": obj_value,
                "variables": solution,
                "iterations": len(steps),
                "equations_latex": equations_latex,
                "steps": steps,
                "explanation": f"Método Simplex: {len(steps)} iteraciones hasta optimalidad"
            })
            
        except Exception as e:
            logger.error(f"Error en _simplex_tableau: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e), "steps": []}

    def _graphical_method(self, model: MathematicalModel) -> Dict[str, Any]:
        """Método gráfico para 2 variables con cálculo correcto de vértices y graficación."""
        try:
            var_names = list(model.variables.keys())
            if len(var_names) != 2:
                return {"success": False, "error": "Método gráfico requiere exactamente 2 variables"}
            
            x_name, y_name = var_names[0], var_names[1]
            x, y = sp.Symbol(x_name, real=True, positive=True), sp.Symbol(y_name, real=True, positive=True)
            symbols = {x_name: x, y_name: y}
            
            # Parsear función objetivo
            obj_expr = sp.sympify(model.objective_function, locals=symbols)
            is_max = model.objective == "max"
            
            # Parsear restricciones estructurales
            structural_constraints = self._filter_nonneg_constraints(model.constraints, var_names)
            constraints_ineq = [self._parse_constraint(c, symbols) for c in structural_constraints]
            constraints_ineq = [c for c in constraints_ineq if c]
            
            if not constraints_ineq:
                feasible_points = [(0, 0)]
            else:
                vertices = {(0.0, 0.0)}
                for lhs, op, rhs_val in constraints_ineq:
                    # Intersecciones con ejes
                    for var, fix_var, fix_val in [(x, y, 0), (y, x, 0)]:
                        try:
                            eq = lhs.subs(fix_var, fix_val) - rhs_val
                            sol = sp.solve(eq, var)
                            if sol:
                                val = self._safe_float_conversion(sol[0])
                                if val >= -self._TOL:
                                    vertices.add((self._safe_float_conversion(sol[0]) if var == x else 0, 
                                                 self._safe_float_conversion(sol[0]) if var == y else 0))
                        except:
                            pass
                
                # Intersecciones entre restricciones
                for i, (lhs1, op1, rhs1) in enumerate(constraints_ineq):
                    for lhs2, op2, rhs2 in constraints_ineq[i+1:]:
                        try:
                            sol = sp.solve([lhs1 - rhs1, lhs2 - rhs2], [x, y])
                            if sol and isinstance(sol, dict):
                                x_val, y_val = self._safe_float_conversion(sol.get(x, 0)), self._safe_float_conversion(sol.get(y, 0))
                                if x_val >= -self._TOL and y_val >= -self._TOL:
                                    vertices.add((x_val, y_val))
                        except:
                            pass
                
                # Filtrar vértices factibles
                feasible_points = []
                for v_x, v_y in vertices:
                    is_feasible = v_x >= -self._TOL and v_y >= -self._TOL
                    for lhs, op, rhs_val in constraints_ineq:
                        val = self._safe_float_conversion(lhs.subs({x: v_x, y: v_y}))
                        rhs_float = self._safe_float_conversion(rhs_val)
                        if (op == "<=" and val > rhs_float + self._FEASIBLE_TOL) or \
                           (op == ">=" and val < rhs_float - self._FEASIBLE_TOL) or \
                           (op == "=" and abs(val - rhs_float) > self._FEASIBLE_TOL):
                            is_feasible = False
                            break
                    if is_feasible:
                        feasible_points.append((v_x, v_y))
            
            if not feasible_points:
                return {"success": False, "error": "No hay región factible"}
            
            # Evaluar objetivo y encontrar óptimo
            evaluated_points = []
            best_value = best_point = None
            for point in feasible_points:
                obj_val = self._safe_float_conversion(obj_expr.subs({x: point[0], y: point[1]}))
                evaluated_points.append({"point": point, "objective": obj_val, "is_optimal": False})
                if best_value is None or (is_max and obj_val > best_value) or (not is_max and obj_val < best_value):
                    best_value, best_point = obj_val, point
            
            for pt in evaluated_points:
                if abs(pt["objective"] - best_value) < self._FEASIBLE_TOL and pt["point"] == best_point:
                    pt["is_optimal"] = True
                    break
            
            solution = {x_name: self._safe_float_conversion(best_point[0]), y_name: self._safe_float_conversion(best_point[1])}
            
            # Extraer información de restricciones y construir matrices A, b
            constraints_info = []
            A = np.zeros((len(structural_constraints), len(var_names)))
            b = np.zeros(len(structural_constraints))
            
            for idx, constraint_str in enumerate(structural_constraints):
                parsed = self._parse_constraint(constraint_str, symbols)
                if parsed:
                    lhs, op, rhs_val = parsed
                    a_coeff = self._safe_float_conversion(lhs.coeff(x, 1) or 0)
                    b_coeff = self._safe_float_conversion(lhs.coeff(y, 1) or 0)
                    constraints_info.append({
                        "constraint": constraint_str,
                        "a": a_coeff,
                        "b": b_coeff,
                        "rhs": self._safe_float_conversion(rhs_val),
                        "operator": op
                    })
                    A[idx, 0] = a_coeff
                    A[idx, 1] = b_coeff
                    b[idx] = self._safe_float_conversion(rhs_val)
            
            # Generar ecuaciones LaTeX con subíndices
            equations_latex = self._generate_equations_latex_graphical(
                structural_constraints, var_names, symbols, A, b
            ) if len(structural_constraints) > 0 else ""
            
            result = {
                "success": True,
                "method": "graphical",
                "status": "optimal",
                "objective_value": best_value,
                "variables": solution,
                "optimal_point": best_point,
                "feasible_points": evaluated_points,
                "constraints_info": constraints_info,
                "equations_latex": equations_latex,
                "steps": [],
                "objective_coefficients": {x_name: self._safe_float_conversion(obj_expr.coeff(x, 1) or 0), 
                                          y_name: self._safe_float_conversion(obj_expr.coeff(y, 1) or 0)},
                "explanation": f"Método Gráfico: Se evaluaron {len(feasible_points)} vértices de la región factible"
            }
            
            # Generar gráfica
            graphication_service = GraphicationService()
            graph_result = graphication_service.generate_graphical_solution(model, result)
            if graph_result.get("success"):
                result["graph"] = {
                    "image": graph_result.get("image"),
                    "vertices_table": graph_result.get("vertices_table"),
                    "solution_block": graph_result.get("solution_block")
                }
            else:
                logger.warning(f"No se pudo generar gráfica: {graph_result.get('error')}")
            
            return self._convert_numpy_types(result)
            
        except Exception as e:
            logger.error(f"Error en _graphical_method: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e), "steps": []}

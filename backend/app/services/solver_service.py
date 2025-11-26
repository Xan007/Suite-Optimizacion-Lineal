"""
SolverService: Implementación didáctica del método Simplex con visualización de tablas.
"""

from typing import Dict, List, Optional, Tuple, Any
import sympy as sp
import numpy as np

from app.schemas.analyze_schema import MathematicalModel
from app.core.logger import logger

try:
    import pulp
except Exception:
    pulp = None


class SolverService:
    """Servicio para resolver problemas de optimización lineal con Simplex didáctico."""

    def __init__(self):
        pass

    def determine_applicable_methods(self, model: MathematicalModel) -> Tuple[List[str], Dict[str, str]]:
        """Retorna métodos sugeridos y no aplicables."""
        suggested: List[str] = ["simplex"]
        not_applicable: Dict[str, str] = {}
        
        if len(model.variables) <= 2:
            suggested.append("graphical")
        else:
            not_applicable["graphical"] = "Más de 2 variables"
        
        return suggested, not_applicable

    def solve(self, model: MathematicalModel, method: str = "simplex") -> Dict[str, Any]:
        """Resuelve usando Simplex tableau con visualización didáctica."""
        try:
            if method == "simplex":
                return self._simplex_tableau(model)
            elif method == "graphical":
                return self._graphical_method(model)
            else:
                return {"success": False, "error": f"Método no soportado: {method}"}
        except Exception as e:
            logger.error(f"Error en solve: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _convert_numpy_types(self, obj: Any) -> Any:
        """Convierte tipos NumPy a tipos nativas de Python para JSON serialización."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj

    def _simplex_tableau(self, model: MathematicalModel) -> Dict[str, Any]:
        """Método Simplex Tableau con tablas en cada iteración."""
        try:
            var_names = list(model.variables.keys())
            n = len(var_names)
            
            # Crear símbolos SymPy
            symbols = {name: sp.Symbol(name, real=True, positive=True) for name in var_names}
            
            # Parsear función objetivo
            obj_expr = sp.sympify(model.objective_function, locals=symbols)
            c = np.array([float(obj_expr.coeff(symbols[v], 1) or 0) for v in var_names])
            is_max = model.objective == "max"
            if not is_max:
                c = -c
            
            # Parsear restricciones
            constraints = model.constraints or []
            A = []
            b = []
            
            for constraint_str in constraints:
                # Filtrar restricciones de no-negatividad
                is_nonneg = False
                for var in var_names:
                    if f"{var} >= 0" in constraint_str or f"{var}<= 0" in constraint_str:
                        is_nonneg = True
                        break
                
                if is_nonneg:
                    continue
                
                # Parsear restricción
                rel = sp.sympify(constraint_str, locals=symbols, evaluate=False)
                if not (hasattr(rel, 'lhs') and hasattr(rel, 'rhs')):
                    continue
                
                lhs = sp.expand(rel.lhs)
                rhs_val = float(rel.rhs)
                
                row = np.array([float(lhs.coeff(symbols[v], 1) or 0) for v in var_names])
                
                # Normalizar si la restricción es >=
                if '>=' in str(rel):
                    row = -row
                    rhs_val = -rhs_val
                
                A.append(row)
                b.append(rhs_val)
            
            if not A:
                return {"success": False, "error": "No hay restricciones estructurales"}
            
            A = np.array(A)
            b = np.array(b)
            m = len(b)  # número de restricciones
            
            # Construir tabla Simplex: [A | I | b]
            tableau = np.hstack([A, np.eye(m), b.reshape(-1, 1)])
            
            # Fila de costos: [-c | 0 | 0]
            obj_row = np.hstack([[-ci for ci in c], np.zeros(m), [0]])
            
            # Base inicial (variables de holgura)
            basis = [f"s{i+1}" for i in range(m)]
            basis_cols = list(range(n, n + m))
            
            steps = []
            iteration = 0
            
            # Tabla inicial
            steps.append({
                "iteration": 0,
                "tableau": tableau.copy(),
                "obj_row": obj_row.copy(),
                "basis": basis[:],
                "basis_cols": basis_cols[:],
                "description": "Tabla Inicial"
            })
            
            # Algoritmo Simplex
            max_iterations = 100
            while iteration < max_iterations:
                iteration += 1
                
                # Encontrar variable entrante (columna con valor más negativo en obj_row)
                entering_col = np.argmin(obj_row[:-1])
                
                if obj_row[entering_col] >= -1e-10:
                    # Óptimo encontrado
                    break
                
                # Encontrar variable saliente (razón mínima positiva)
                ratios = []
                for i in range(m):
                    if tableau[i, entering_col] > 1e-10:
                        ratios.append(tableau[i, -1] / tableau[i, entering_col])
                    else:
                        ratios.append(float('inf'))
                
                leaving_row = np.argmin(ratios)
                
                if ratios[leaving_row] == float('inf'):
                    return {"success": False, "error": "Problema ilimitado"}
                
                # Guardar estado ANTES del pivote
                tableau_before = tableau.copy()
                obj_row_before = obj_row.copy()
                basis_before = basis[:]
                
                pivot = tableau[leaving_row, entering_col]
                
                # Pivoteo
                tableau[leaving_row] /= pivot
                for i in range(m):
                    if i != leaving_row:
                        factor = tableau[i, entering_col]
                        tableau[i] -= factor * tableau[leaving_row]
                
                factor = obj_row[entering_col]
                # Actualizar fila de costos: obj_row = obj_row - factor * fila_pivote
                pivot_row_extended = np.hstack([tableau[leaving_row]])
                obj_row = obj_row - factor * pivot_row_extended
                
                # Actualizar base
                entering_name = var_names[entering_col] if entering_col < n else f"s{entering_col - n + 1}"
                leaving_name = basis[leaving_row]
                basis[leaving_row] = entering_name
                basis_cols[leaving_row] = entering_col
                
                steps.append({
                    "iteration": iteration,
                    "tableau_before": tableau_before.copy(),
                    "obj_row_before": obj_row_before.copy(),
                    "basis_before": basis_before,
                    "tableau_after": tableau.copy(),
                    "obj_row_after": obj_row.copy(),
                    "basis_after": basis[:],
                    "basis_cols": basis_cols[:],
                    "entering": entering_name,
                    "leaving": leaving_name,
                    "leaving_row": leaving_row,
                    "entering_col": entering_col,
                    "pivot_element": pivot,
                    "description": f"Entra {entering_name}, Sale {leaving_name}"
                })
            
            # Extraer solución
            solution = {v: 0.0 for v in var_names}
            for i, basis_var in enumerate(basis):
                if basis_var in var_names:
                    solution[basis_var] = float(tableau[i, -1])
            
            # Calcular valor objetivo
            obj_value = float(obj_row[-1])
            if not is_max:
                obj_value = -obj_value
            
            # Construir respuesta con pasos formateados
            formatted_steps = []
            
            # Pasos iterativos (omitir tabla inicial de índice 0, comenzar desde iteración 1)
            for step in steps[1:]:
                formatted_step = {
                    "iteration": step['iteration'],
                    "type": "iteration",
                    "description": step['description'],
                    "entering_variable": step['entering'],
                    "leaving_variable": step['leaving'],
                    "pivot_row": int(step['leaving_row']),
                    "leaving_row": int(step['leaving_row']),
                    "entering_col": int(step['entering_col']),
                    "pivot_column": int(step['entering_col']),
                    "pivot_element": float(step['pivot_element']),
                    # ANTES del pivote
                    "tableau_before": step['tableau_before'].tolist(),
                    "obj_row_before": step['obj_row_before'].tolist(),
                    "basis_before": step['basis_before'],
                    # DESPUÉS del pivote
                    "tableau_after": step['tableau_after'].tolist(),
                    "obj_row_after": step['obj_row_after'].tolist(),
                    "basis_after": step['basis_after'],
                    # Info para renderizado
                    "var_names": var_names,
                    "slack_names": [f"s{i+1}" for i in range(m)]
                }
                formatted_steps.append(formatted_step)
            
            result = {
                "success": True,
                "method": "simplex",
                "status": "optimal",
                "objective_value": obj_value,
                "variables": solution,
                "iterations": iteration,
                "steps": formatted_steps,
                "explanation": f"Método Simplex: {iteration} iteraciones hasta optimalidad"
            }
            
            return self._convert_numpy_types(result)
            
        except Exception as e:
            logger.error(f"Error en _simplex_tableau: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _graphical_method(self, model: MathematicalModel) -> Dict[str, Any]:
        """Método gráfico para 2 variables con cálculo correcto de vértices."""
        try:
            var_names = list(model.variables.keys())
            if len(var_names) != 2:
                return {"success": False, "error": "Método gráfico requiere exactamente 2 variables"}
            
            x_name, y_name = var_names[0], var_names[1]
            x = sp.Symbol(x_name, real=True, positive=True)
            y = sp.Symbol(y_name, real=True, positive=True)
            symbols = {x_name: x, y_name: y}
            
            # Parsear función objetivo
            obj_expr = sp.sympify(model.objective_function, locals=symbols)
            is_max = model.objective == "max"
            
            # Parsear restricciones estructurales (filtrar no-negatividad)
            constraints_data = []
            for constraint_str in model.constraints:
                # Filtrar restricciones de no-negatividad
                if f"{x_name} >= 0" in constraint_str or f"{y_name} >= 0" in constraint_str:
                    continue
                
                constraints_data.append(constraint_str)
            
            if not constraints_data:
                # Solo no-negatividad
                feasible_points = [(0, 0)]
            else:
                # Construir lista de restricciones como desigualdades lineales
                constraints_ineq = []
                for constraint_str in constraints_data:
                    try:
                        rel = sp.sympify(constraint_str, locals=symbols, evaluate=False)
                        if hasattr(rel, 'lhs') and hasattr(rel, 'rhs'):
                            lhs = sp.expand(rel.lhs)
                            rhs_val = rel.rhs
                            
                            # Obtener operador
                            rel_type = str(type(rel).__name__)
                            if "LessThan" in rel_type:
                                op = "<="
                            elif "GreaterThan" in rel_type:
                                op = ">="
                            elif "Equality" in rel_type:
                                op = "="
                            else:
                                op = "<="
                            
                            constraints_ineq.append((lhs, op, rhs_val))
                    except:
                        pass
                
                # Calcular vértices: intersecciones de pares de restricciones + ejes
                vertices = set()
                
                # Origen
                vertices.add((0.0, 0.0))
                
                # Intersección con eje x (y=0)
                for lhs, op, rhs_val in constraints_ineq:
                    eq_x_axis = lhs.subs(y, 0) - rhs_val
                    try:
                        sol_x = sp.solve(eq_x_axis, x)
                        if sol_x:
                            x_val = float(sol_x[0])
                            if x_val >= -1e-10:  # x >= 0
                                vertices.add((x_val, 0.0))
                    except:
                        pass
                
                # Intersección con eje y (x=0)
                for lhs, op, rhs_val in constraints_ineq:
                    eq_y_axis = lhs.subs(x, 0) - rhs_val
                    try:
                        sol_y = sp.solve(eq_y_axis, y)
                        if sol_y:
                            y_val = float(sol_y[0])
                            if y_val >= -1e-10:  # y >= 0
                                vertices.add((0.0, y_val))
                    except:
                        pass
                
                # Intersecciones entre pares de restricciones
                for i in range(len(constraints_ineq)):
                    for j in range(i + 1, len(constraints_ineq)):
                        lhs1, op1, rhs1 = constraints_ineq[i]
                        lhs2, op2, rhs2 = constraints_ineq[j]
                        
                        eq1 = lhs1 - rhs1
                        eq2 = lhs2 - rhs2
                        
                        try:
                            sol = sp.solve([eq1, eq2], [x, y])
                            if sol and isinstance(sol, dict):
                                x_val = float(sol.get(x, 0))
                                y_val = float(sol.get(y, 0))
                                if x_val >= -1e-10 and y_val >= -1e-10:
                                    vertices.add((x_val, y_val))
                        except:
                            pass
                
                # Filtrar vértices que satisfacen todas las restricciones
                feasible_points = []
                for v_x, v_y in vertices:
                    is_feasible = True
                    
                    # Verificar no-negatividad
                    if v_x < -1e-10 or v_y < -1e-10:
                        is_feasible = False
                    
                    # Verificar restricciones estructurales
                    for lhs, op, rhs_val in constraints_ineq:
                        val = float(lhs.subs({x: v_x, y: v_y}))
                        rhs_float = float(rhs_val)
                        
                        if op == "<=":
                            if val > rhs_float + 1e-6:
                                is_feasible = False
                                break
                        elif op == ">=":
                            if val < rhs_float - 1e-6:
                                is_feasible = False
                                break
                        elif op == "=":
                            if abs(val - rhs_float) > 1e-6:
                                is_feasible = False
                                break
                    
                    if is_feasible:
                        feasible_points.append((v_x, v_y))
            
            if not feasible_points:
                return {"success": False, "error": "No hay región factible"}
            
            # Evaluar objetivo en cada vértice
            evaluated_points = []
            best_value = None
            best_point = None
            
            for point in feasible_points:
                obj_val = float(obj_expr.subs({x: point[0], y: point[1]}))
                evaluated_points.append({
                    "point": point,
                    "objective": obj_val,
                    "is_optimal": False
                })
                
                if best_value is None:
                    best_value = obj_val
                    best_point = point
                else:
                    if (is_max and obj_val > best_value) or (not is_max and obj_val < best_value):
                        best_value = obj_val
                        best_point = point
            
            # Marcar punto óptimo
            for pt in evaluated_points:
                if abs(pt["objective"] - best_value) < 1e-6 and pt["point"] == best_point:
                    pt["is_optimal"] = True
                    break
            
            solution = {x_name: float(best_point[0]), y_name: float(best_point[1])}
            
            # Extraer información de restricciones para graficar
            constraints_info = []
            for constraint_str in constraints_data:
                try:
                    rel = sp.sympify(constraint_str, locals=symbols, evaluate=False)
                    if hasattr(rel, 'lhs') and hasattr(rel, 'rhs'):
                        lhs = sp.expand(rel.lhs)
                        rhs_val = rel.rhs
                        
                        # Obtener coeficientes a, b para: a*x + b*y ≤ c
                        coeff_x = float(lhs.coeff(x, 1) or 0)
                        coeff_y = float(lhs.coeff(y, 1) or 0)
                        rhs_float = float(rhs_val)
                        
                        # Obtener operador
                        rel_type = str(type(rel).__name__)
                        if "LessThan" in rel_type:
                            op = "<="
                        elif "GreaterThan" in rel_type:
                            op = ">="
                        elif "Equality" in rel_type:
                            op = "="
                        else:
                            op = "<="
                        
                        constraints_info.append({
                            "constraint": constraint_str,
                            "a": coeff_x,
                            "b": coeff_y,
                            "rhs": rhs_float,
                            "operator": op
                        })
                except:
                    pass
            
            # Extraer coeficientes de la función objetivo para las curvas de nivel
            obj_coeff_x = float(obj_expr.coeff(x, 1) or 0)
            obj_coeff_y = float(obj_expr.coeff(y, 1) or 0)
            
            return {
                "success": True,
                "method": "graphical",
                "status": "optimal",
                "objective_value": best_value,
                "variables": solution,
                "optimal_point": best_point,
                "feasible_points": evaluated_points,
                "constraints_info": constraints_info,
                "objective_coefficients": {x_name: obj_coeff_x, y_name: obj_coeff_y},
                "explanation": f"Método Gráfico: Se evaluaron {len(feasible_points)} vértices de la región factible"
            }
            
        except Exception as e:
            logger.error(f"Error en _graphical_method: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

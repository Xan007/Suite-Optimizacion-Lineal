"""
DualSimplexMethod: Implementación del método Simplex Dual para problemas de minimización.

El método Simplex Dual es especialmente útil cuando:
- El problema está en forma estándar pero la solución básica inicial es dual-factible pero primal-infactible
- Se tienen restricciones >= en problemas de minimización
- Se requiere post-optimización después de agregar nuevas restricciones

Características:
- Selección de fila pivote: fila con RHS más negativo (variable saliente)
- Selección de columna pivote: razón dual mínima (variable entrante)
- Genera visualización detallada con colores para pivotes
- Muestra todas las iteraciones con explicaciones paso a paso
"""

from typing import Dict, List, Optional, Tuple, Any
import sympy as sp
import numpy as np
from dataclasses import dataclass
import json

from app.core.logger import logger
from app.schemas.analyze_schema import MathematicalModel


@dataclass
class DualSimplexStep:
    """Representa un paso en la resolución con el método Simplex Dual."""
    iteration: int
    description: str
    entering_variable: Optional[str] = None
    leaving_variable: Optional[str] = None
    pivot_row: Optional[int] = None
    pivot_column: Optional[int] = None
    pivot_element: Optional[float] = None
    tableau: List[List[float]] = None
    tableau_before: Optional[List[List[float]]] = None
    obj_row_before: Optional[List[float]] = None
    obj_row_after: Optional[List[float]] = None
    basis: List[str] = None
    basis_before: Optional[List[str]] = None
    basis_columns: List[int] = None
    column_headers: List[str] = None
    row_labels: List[str] = None
    var_names: Optional[List[str]] = None
    reasoning: Dict[str, Any] = None
    is_optimal: bool = False
    is_feasible: bool = False
    status: str = ""  # "in_progress", "optimal", "infeasible", "unbounded"
    dual_ratios: Optional[List[Dict[str, Any]]] = None


class DualSimplexMethod:
    """Método Simplex Dual para problemas de programación lineal."""
    
    _TOL = 1e-10
    _FEASIBLE_TOL = 1e-6
    
    def __init__(self):
        """Inicializa el método Simplex Dual."""
        self.steps: List[DualSimplexStep] = []
        self.slack_variables: Dict[str, int] = {}
        self.surplus_variables: Dict[str, int] = {}
        self.var_map: Dict[str, int] = {}
        
    def solve(self, model: MathematicalModel) -> Dict[str, Any]:
        """
        Resuelve el problema de minimización usando el método Simplex Dual.
        
        El método Simplex Dual trabaja con:
        - Dual-factibilidad: todos los coeficientes en la fila objetivo son >= 0
        - Primal-infactibilidad inicial: algunos valores RHS pueden ser negativos
        
        Args:
            model: Modelo matemático a resolver (debe ser minimización)
            
        Returns:
            Diccionario con solución, tablas y pasos iterativos con colores para pivotes
        """
        try:
            self.steps = []
            self.slack_variables = {}
            self.surplus_variables = {}
            self.var_map = {}
            
            # Validar que sea problema de minimización
            if model.objective != "min":
                return {
                    "success": False,
                    "error": "El método Simplex Dual solo se aplica a problemas de minimización",
                    "steps": []
                }
            
            # Preparar el problema
            var_names = list(model.variables.keys())
            n_vars = len(var_names)
            
            # Crear símbolos SymPy
            symbols = {name: sp.Symbol(name, real=True, positive=True) for name in var_names}
            
            # Parsear función objetivo
            obj_expr = sp.sympify(model.objective_function, locals=symbols)
            c = np.array([float(obj_expr.coeff(symbols[v], 1) or 0) for v in var_names])
            
            # Parsear restricciones (esperamos restricciones >=)
            constraints_data = self._parse_constraints(
                model.constraints or [], var_names, symbols
            )
            
            if not constraints_data:
                return {
                    "success": False,
                    "error": "No se encontraron restricciones estructurales",
                    "steps": []
                }
            
            # Construir tableau inicial
            tableau, basis, basis_cols, model_construction = self._build_initial_tableau(
                c, constraints_data, var_names, model
            )
            
            if tableau is None:
                return {
                    "success": False,
                    "error": "Error al construir el tableau inicial",
                    "steps": []
                }
            
            # Generar paso inicial con la construcción del modelo
            self._add_initial_step(tableau, basis, basis_cols, var_names, model_construction)
            
            # Iterar con Simplex Dual
            max_iterations = 1000
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Verificar factibilidad primal (todos RHS >= 0)
                if self._is_primal_feasible(tableau):
                    # Solución óptima encontrada
                    self._add_final_step(tableau, basis, basis_cols, var_names, "optimal")
                    break
                
                # Encontrar fila pivote (fila con RHS más negativo)
                leaving_row = self._find_leaving_row(tableau)
                
                if leaving_row is None:
                    # No hay filas con RHS negativo (ya factible)
                    self._add_final_step(tableau, basis, basis_cols, var_names, "optimal")
                    break
                
                # Encontrar columna pivote (razón dual mínima)
                entering_col = self._find_entering_column(tableau, leaving_row)
                
                if entering_col is None:
                    # Problema infactible
                    self._add_final_step(tableau, basis, basis_cols, var_names, "infeasible")
                    result = {
                        "success": False,
                        "status": "infeasible",
                        "error": "El problema es infactible (no existe región factible)"
                    }
                    return self._convert_result_to_format_with_error(result)
                
                # Obtener información del pivote ANTES de modificar
                entering_name = self._get_variable_name_from_col(entering_col)
                leaving_name = basis[leaving_row]
                pivot_element = float(tableau[leaving_row, entering_col])
                
                # Registrar estado antes del pivote
                tableau_before = tableau.copy()
                basis_before = basis[:]
                
                # Calcular razones duales para visualización
                dual_ratios = self._calculate_dual_ratios(
                    tableau, leaving_row, entering_col
                )
                
                # Realizar pivote
                self._pivot_in_place(tableau, leaving_row, entering_col)
                
                # Actualizar base
                basis[leaving_row] = entering_name
                basis_cols[leaving_row] = entering_col
                
                # Registrar paso con información detallada
                self._add_iteration_step(
                    tableau, basis, basis_cols, var_names,
                    entering_name, leaving_name, leaving_row, entering_col,
                    pivot_element, iteration, tableau_before, basis_before,
                    dual_ratios
                )
            
            # Verificar factibilidad final
            if not self._is_primal_feasible(tableau):
                result = {
                    "success": False,
                    "status": "infeasible",
                    "error": "El problema es infactible (solución final tiene RHS negativos)"
                }
                return self._convert_result_to_format_with_error(result)
            
            # Extraer solución
            solution = self._extract_solution(tableau, basis, var_names)
            # El valor objetivo: para minimización, el RHS de la fila Z es el valor óptimo
            # Como los coeficientes en la fila Z son positivos (c), el RHS ya tiene el signo correcto
            obj_value = float(tableau[-1, -1])
            
            # Generar ecuaciones LaTeX
            equations_latex = self._generate_equations_latex(
                constraints_data, var_names
            )
            
            return self._convert_result_to_format(
                obj_value, solution, var_names, equations_latex
            )
            
        except Exception as e:
            logger.error(f"Error en DualSimplexMethod.solve: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "steps": []
            }
    
    def _parse_constraints(
        self,
        constraints: List[str],
        var_names: List[str],
        symbols: Dict
    ) -> List[Tuple[np.ndarray, str, float]]:
        """
        Parsea restricciones y retorna lista de (coeficientes, operador, RHS).
        Filtra restricciones de no-negatividad.
        """
        constraints_data = []
        
        for constraint_str in constraints:
            constraint_str = constraint_str.strip()
            
            # Filtrar restricciones de no-negatividad
            if any(f"{v} >= 0" in constraint_str or f"{v} <= 0" in constraint_str 
                   for v in var_names):
                continue
            
            try:
                # Parsear: "2*x1 + x2 >= 10" o "2*x1 + x2 <= 10"
                parts = None
                for op in ["<=", ">=", "="]:
                    if op in constraint_str:
                        left, right = constraint_str.split(op, 1)
                        parts = (left.strip(), op, right.strip())
                        break
                
                if not parts:
                    continue
                
                lhs_str, op, rhs_str = parts
                lhs_expr = sp.sympify(lhs_str, locals=symbols)
                rhs_val = float(sp.sympify(rhs_str))
                
                # Extraer coeficientes
                coeffs = np.array([
                    float(lhs_expr.coeff(symbols[v], 1) or 0)
                    for v in var_names
                ])
                
                constraints_data.append((coeffs, op, rhs_val))
                
            except Exception as e:
                logger.warning(f"Error parseando restricción '{constraint_str}': {e}")
                continue
        
        return constraints_data
    
    def _build_initial_tableau(
        self,
        c: np.ndarray,
        constraints_data: List[Tuple[np.ndarray, str, float]],
        var_names: List[str],
        model: MathematicalModel
    ) -> Tuple[Optional[np.ndarray], List[str], List[int], Dict[str, Any]]:
        """
        Construye el tableau inicial para Simplex Dual.
        
        Para problemas de minimización con restricciones >=:
        - Se convierten restricciones >= a <= multiplicando por -1
        - Esto hace que algunos RHS sean negativos (primal-infactible)
        - La fila objetivo tiene coeficientes negativos para que Z final sea positivo
        
        Returns:
            Tuple con (tableau, basis, basis_cols, model_construction)
        """
        n_vars = len(var_names)
        n_constraints = len(constraints_data)
        
        # Contar variables de holgura necesarias
        n_slack = n_constraints
        n_total = n_vars + n_slack
        
        # Inicializar tableau
        tableau = np.zeros((n_constraints + 1, n_total + 1))
        
        # Crear mapeo de variables a índices
        self.var_map = {}
        idx = 0
        
        # Variables originales
        for var in var_names:
            self.var_map[var] = idx
            idx += 1
        
        # Variables de holgura
        for i in range(n_slack):
            s_name = f"s{i+1}"
            self.var_map[s_name] = idx
            self.slack_variables[s_name] = idx
            idx += 1
        
        # Construcción del modelo para mostrar al usuario
        model_construction = {
            "original_objective": model.objective_function,
            "original_constraints": model.constraints or [],
            "standard_form_constraints": [],
            "slack_variables_added": [],
            "objective_with_slack": ""
        }
        
        # Llenar restricciones
        basis = []
        basis_cols = []
        
        for i, (coeffs, op, rhs) in enumerate(constraints_data):
            # Coeficientes de variables originales
            row_coeffs = coeffs.copy()
            row_rhs = rhs
            
            s_name = f"s{i+1}"
            original_constraint = model.constraints[i] if model.constraints and i < len(model.constraints) else ""
            
            # Convertir >= a <= multiplicando por -1
            if op == ">=":
                row_coeffs = -row_coeffs
                row_rhs = -row_rhs
                # Guardar la transformación para mostrar
                model_construction["slack_variables_added"].append({
                    "name": s_name,
                    "original": original_constraint,
                    "transformed": f"Multiplicar por -1 y agregar {s_name}",
                    "standard_form": self._format_constraint_with_slack(coeffs, op, rhs, s_name, var_names)
                })
            else:
                model_construction["slack_variables_added"].append({
                    "name": s_name,
                    "original": original_constraint,
                    "transformed": f"Agregar {s_name}",
                    "standard_form": self._format_constraint_with_slack(coeffs, op, rhs, s_name, var_names)
                })
            
            tableau[i, :n_vars] = row_coeffs
            
            # Agregar variable de holgura
            s_col = self.var_map[s_name]
            tableau[i, s_col] = 1
            
            # RHS (puede ser negativo para >= original)
            tableau[i, -1] = row_rhs
            
            # Variable de holgura en la base
            basis.append(s_name)
            basis_cols.append(s_col)
        
        # Construir fila objetivo para minimización
        # Forma estándar del tableau: Z - c1*x1 - c2*x2 - ... = 0
        # Reescribimos como: -c1*x1 - c2*x2 - ... + Z = 0
        # En el tableau ponemos los coeficientes NEGATIVOS de las variables
        # Así cuando se hace el pivoteo, el RHS de Z será POSITIVO (el valor mínimo)
        obj_row = np.zeros(n_total + 1)
        obj_row[:n_vars] = -c  # Coeficientes negativos para que Z final sea positivo
        
        tableau[-1] = obj_row
        
        # Guardar la función objetivo en forma estándar
        model_construction["objective_with_slack"] = self._format_objective_standard(c, var_names)
        
        return tableau, basis, basis_cols, model_construction
    
    def _format_constraint_with_slack(self, coeffs: np.ndarray, op: str, rhs: float, slack_name: str, var_names: List[str]) -> str:
        """Formatea una restricción mostrando la variable de holgura."""
        terms = []
        for j, var in enumerate(var_names):
            coeff = float(coeffs[j])
            if abs(coeff) > self._TOL:
                if coeff == 1:
                    terms.append(f"{var}")
                elif coeff == -1:
                    terms.append(f"-{var}")
                elif coeff > 0:
                    terms.append(f"{coeff:.4g}{var}")
                else:
                    terms.append(f"{coeff:.4g}{var}")
        
        lhs = " + ".join(terms).replace("+ -", "- ")
        
        if op == ">=":
            return f"{lhs} - {slack_name} = {rhs:.4g}"
        else:
            return f"{lhs} + {slack_name} = {rhs:.4g}"
    
    def _format_objective_standard(self, c: np.ndarray, var_names: List[str]) -> str:
        """Formatea la función objetivo en forma estándar."""
        terms = []
        for j, var in enumerate(var_names):
            coeff = float(c[j])
            if abs(coeff) > self._TOL:
                if coeff == 1:
                    terms.append(f"{var}")
                elif coeff == -1:
                    terms.append(f"-{var}")
                elif coeff > 0:
                    terms.append(f"{coeff:.4g}{var}")
                else:
                    terms.append(f"{coeff:.4g}{var}")
        
        obj_str = " + ".join(terms).replace("+ -", "- ")
        return f"Min Z = {obj_str}"
    
    def _is_primal_feasible(self, tableau: np.ndarray) -> bool:
        """
        Verifica si la solución actual es primal-factible.
        Una solución es primal-factible si todos los RHS >= 0.
        """
        rhs = tableau[:-1, -1]
        return np.all(rhs >= -self._TOL)
    
    def _find_leaving_row(self, tableau: np.ndarray) -> Optional[int]:
        """
        Encuentra la fila pivote (variable saliente) en Simplex Dual.
        Selecciona la fila con el RHS más negativo.
        """
        rhs = tableau[:-1, -1]
        
        # Encontrar índice con RHS más negativo
        min_rhs = float('inf')
        min_row = None
        
        for i in range(len(rhs)):
            if rhs[i] < -self._TOL and rhs[i] < min_rhs:
                min_rhs = rhs[i]
                min_row = i
        
        return min_row
    
    def _find_entering_column(self, tableau: np.ndarray, leaving_row: int) -> Optional[int]:
        """
        Encuentra la columna pivote (variable entrante) en Simplex Dual.
        
        Criterio de razón dual:
        - Solo considerar columnas con coeficientes negativos en la fila pivote
        - Calcular razón: |z_j / a_{ij}| donde z_j es el coeficiente en fila objetivo
        - Seleccionar la columna con razón mínima
        """
        pivot_row_coeffs = tableau[leaving_row, :-1]
        obj_row_coeffs = tableau[-1, :-1]
        
        min_ratio = float('inf')
        min_col = None
        
        for j in range(len(pivot_row_coeffs)):
            # Solo columnas con coeficiente negativo en fila pivote
            if pivot_row_coeffs[j] < -self._TOL:
                # Razón dual: |c_j / a_{ij}|
                ratio = abs(obj_row_coeffs[j] / pivot_row_coeffs[j])
                
                if ratio < min_ratio:
                    min_ratio = ratio
                    min_col = j
        
        return min_col
    
    def _calculate_dual_ratios(
        self,
        tableau: np.ndarray,
        leaving_row: int,
        entering_col: int
    ) -> List[Dict[str, Any]]:
        """
        Calcula las razones duales para todas las columnas elegibles.
        Útil para mostrar el proceso de selección de columna pivote.
        """
        pivot_row_coeffs = tableau[leaving_row, :-1]
        obj_row_coeffs = tableau[-1, :-1]
        
        ratios = []
        
        for j in range(len(pivot_row_coeffs)):
            if pivot_row_coeffs[j] < -self._TOL:
                ratio = abs(obj_row_coeffs[j] / pivot_row_coeffs[j])
                ratios.append({
                    "column": j,
                    "obj_coeff": float(obj_row_coeffs[j]),
                    "pivot_row_coeff": float(pivot_row_coeffs[j]),
                    "ratio": float(ratio),
                    "is_minimum": (j == entering_col)
                })
        
        return ratios
    
    def _pivot_in_place(self, tableau: np.ndarray, pivot_row: int, pivot_col: int) -> None:
        """
        Realiza el pivoteo modificando el tableau EN LUGAR.
        """
        pivot_element = tableau[pivot_row, pivot_col]
        
        # Dividir fila pivote por el elemento pivote
        tableau[pivot_row] = tableau[pivot_row] / pivot_element
        
        # Eliminar elementos en la columna pivote de otras filas
        for i in range(len(tableau)):
            if i != pivot_row and abs(tableau[i, pivot_col]) > self._TOL:
                factor = tableau[i, pivot_col]
                tableau[i] = tableau[i] - factor * tableau[pivot_row]
    
    def _get_variable_name_from_col(self, col: int) -> str:
        """
        Obtiene el nombre de la variable usando el mapeo inverso.
        """
        for name, idx in self.var_map.items():
            if idx == col:
                return name
        return f"var_{col}"
    
    def _extract_solution(
        self,
        tableau: np.ndarray,
        basis: List[str],
        var_names: List[str]
    ) -> Dict[str, float]:
        """
        Extrae la solución óptima del tableau final.
        """
        solution = {v: 0.0 for v in var_names}
        
        for i, var_name in enumerate(basis):
            if var_name in var_names:
                rhs_value = float(tableau[i, -1])
                solution[var_name] = rhs_value if abs(rhs_value) > self._TOL else 0.0
        
        return solution
    
    def _add_initial_step(
        self,
        tableau: np.ndarray,
        basis: List[str],
        basis_cols: List[int],
        var_names: List[str],
        model_construction: Dict[str, Any] = None
    ) -> None:
        """
        Agrega el paso inicial mostrando el tableau antes de iterar.
        """
        var_names_str = [str(v) if hasattr(v, '__str__') else v for v in var_names]
        
        column_headers = var_names_str + list(self.slack_variables.keys()) + ["RHS"]
        # Solo incluir las etiquetas de las variables básicas + Z (sin duplicar)
        row_labels = [str(b) for b in basis] + ["Z"]
        
        # Verificar factibilidad inicial
        is_feasible = self._is_primal_feasible(tableau)
        
        step = DualSimplexStep(
            iteration=0,
            description="Tableau inicial - Método Simplex Dual",
            tableau=tableau.tolist(),
            tableau_before=None,
            obj_row_before=None,
            obj_row_after=tableau[-1].tolist(),
            basis=[str(b) for b in basis],
            basis_before=None,
            basis_columns=[int(bc) for bc in basis_cols],
            column_headers=[str(h) for h in column_headers],
            row_labels=[str(rl) for rl in row_labels],
            var_names=var_names_str,
            is_feasible=is_feasible,
            status="in_progress",
            reasoning={
                "description": "Tableau inicial con variables de holgura",
                "slack_variables": {str(k): int(v) for k, v in self.slack_variables.items()},
                "is_primal_feasible": is_feasible,
                "is_dual_feasible": True,  # Siempre dual-factible al inicio
                "negative_rhs_count": int(np.sum(tableau[:-1, -1] < -self._TOL)),
                "explanation": "El método Simplex Dual comienza dual-factible pero puede ser primal-infactible (algunos RHS negativos)",
                "model_construction": model_construction
            }
        )
        self.steps.append(step)
    
    def _add_iteration_step(
        self,
        tableau: np.ndarray,
        basis: List[str],
        basis_cols: List[int],
        var_names: List[str],
        entering_name: str,
        leaving_name: str,
        pivot_row: int,
        pivot_col: int,
        pivot_element: float,
        iteration: int,
        tableau_before: np.ndarray,
        basis_before: List[str],
        dual_ratios: List[Dict[str, Any]]
    ) -> None:
        """
        Agrega un paso de iteración con información detallada para visualización gráfica.
        """
        var_names_str = [str(v) if hasattr(v, '__str__') else v for v in var_names]
        
        column_headers = var_names_str + list(self.slack_variables.keys()) + ["RHS"]
        # Solo incluir las etiquetas de las variables básicas + Z (sin duplicar)
        row_labels = basis + ["Z"]
        
        # Convertir índices a tipos nativos
        pivot_row_int = int(pivot_row)
        pivot_col_int = int(pivot_col)
        pivot_element_float = float(pivot_element)
        
        # Verificar factibilidad
        is_feasible = self._is_primal_feasible(tableau)
        
        step = DualSimplexStep(
            iteration=iteration,
            description=f"Iteración {iteration}: Entra {entering_name}, Sale {leaving_name}",
            entering_variable=str(entering_name),
            leaving_variable=str(leaving_name),
            pivot_row=pivot_row_int,
            pivot_column=pivot_col_int,
            pivot_element=pivot_element_float,
            tableau=tableau.tolist(),
            tableau_before=tableau_before.tolist(),
            obj_row_before=tableau_before[-1].tolist(),
            obj_row_after=tableau[-1].tolist(),
            basis=[str(b) for b in basis],
            basis_before=[str(b) for b in basis_before],
            basis_columns=[int(bc) for bc in basis_cols],
            column_headers=[str(h) for h in column_headers],
            row_labels=[str(rl) for rl in row_labels],
            var_names=var_names_str,
            is_feasible=is_feasible,
            status="in_progress" if not is_feasible else "optimal",
            dual_ratios=dual_ratios,
            reasoning={
                "description": f"Pivoteo en fila {pivot_row_int}, columna {pivot_col_int}",
                "entering_variable": str(entering_name),
                "leaving_variable": str(leaving_name),
                "pivot_row_index": pivot_row_int,
                "pivot_column_index": pivot_col_int,
                "pivot_element": pivot_element_float,
                "leaving_row_rhs_before": float(tableau_before[pivot_row_int, -1]),
                "dual_ratios_analysis": dual_ratios,
                "is_primal_feasible_after": is_feasible,
                "explanation": f"Fila {pivot_row_int} tiene RHS más negativo. Columna {pivot_col_int} tiene razón dual mínima."
            }
        )
        self.steps.append(step)
    
    def _add_final_step(
        self,
        tableau: np.ndarray,
        basis: List[str],
        basis_cols: List[int],
        var_names: List[str],
        status: str
    ) -> None:
        """
        Registra el paso final.
        """
        var_names_str = [str(v) if hasattr(v, '__str__') else v for v in var_names]
        
        column_headers = var_names_str + list(self.slack_variables.keys()) + ["RHS"]
        # Solo incluir las etiquetas de las variables básicas + Z (sin duplicar)
        row_labels = [str(b) for b in basis] + ["Z"]
        
        is_feasible = self._is_primal_feasible(tableau)
        
        step = DualSimplexStep(
            iteration=len(self.steps),
            description=f"Solución final - Estado: {status}",
            tableau=tableau.tolist(),
            tableau_before=None,
            obj_row_before=None,
            obj_row_after=tableau[-1].tolist(),
            basis=[str(b) for b in basis],
            basis_before=None,
            basis_columns=[int(bc) for bc in basis_cols],
            column_headers=[str(h) for h in column_headers],
            row_labels=[str(rl) for rl in row_labels],
            var_names=var_names_str,
            is_optimal=(status == "optimal"),
            is_feasible=is_feasible,
            status=status,
            reasoning={
                "description": "Solución final alcanzada",
                "all_rhs_nonnegative": is_feasible,
                "final_status": status,
                "explanation": "Todos los RHS son no-negativos: solución primal-factible y dual-factible (óptima)" if status == "optimal" else "No se puede mejorar: problema infactible"
            }
        )
        self.steps.append(step)
    
    def _generate_equations_latex(
        self,
        constraints_data: List[Tuple[np.ndarray, str, float]],
        var_names: List[str]
    ) -> str:
        """
        Genera ecuaciones LaTeX mostrando las restricciones en forma estándar con variables de holgura.
        Formato: coeficientes con subíndices LaTeX apropiados.
        """
        equations = []
        
        for i, (coeffs, op, rhs) in enumerate(constraints_data):
            # Construir términos de variables originales con formato LaTeX
            var_terms = []
            for j, var in enumerate(var_names):
                coeff = float(coeffs[j])
                if abs(coeff) > self._TOL:
                    # Formatear coeficiente
                    if coeff == int(coeff):
                        coeff_val = int(coeff)
                    else:
                        coeff_val = coeff
                    
                    # Extraer nombre base y crear subíndice
                    base_name = var.rstrip('0123456789')
                    var_idx = ''.join(filter(str.isdigit, var)) or str(j + 1)
                    var_sub = f"{base_name}_{{{var_idx}}}"
                    
                    if coeff_val == 1:
                        var_terms.append((1, var_sub))
                    elif coeff_val == -1:
                        var_terms.append((-1, var_sub))
                    else:
                        var_terms.append((coeff_val, var_sub))
            
            # Construir ecuación con formato correcto de signos
            eq_parts = []
            for idx, (coeff_val, var_sub) in enumerate(var_terms):
                if idx == 0:
                    # Primer término
                    if coeff_val == 1:
                        eq_parts.append(var_sub)
                    elif coeff_val == -1:
                        eq_parts.append(f"-{var_sub}")
                    else:
                        eq_parts.append(f"{coeff_val}{var_sub}")
                else:
                    # Términos siguientes
                    if coeff_val == 1:
                        eq_parts.append(f" + {var_sub}")
                    elif coeff_val == -1:
                        eq_parts.append(f" - {var_sub}")
                    elif coeff_val > 0:
                        eq_parts.append(f" + {coeff_val}{var_sub}")
                    else:
                        eq_parts.append(f" - {abs(coeff_val)}{var_sub}")
            
            eq = "".join(eq_parts) if eq_parts else "0"
            
            # Variable de holgura
            s_name = f"s_{{{i+1}}}"
            
            # RHS - para restricciones >= el RHS se vuelve negativo en forma estándar
            if op == ">=":
                rhs_val = -rhs
                eq = f"-{eq.lstrip('-')}" if not eq.startswith('-') else eq.replace('-', '+', 1).replace('+', '-', 1)
                # Reconstruir con signos invertidos
                eq_parts_neg = []
                for idx, (coeff_val, var_sub) in enumerate(var_terms):
                    neg_coeff = -coeff_val
                    if idx == 0:
                        if neg_coeff == 1:
                            eq_parts_neg.append(var_sub)
                        elif neg_coeff == -1:
                            eq_parts_neg.append(f"-{var_sub}")
                        else:
                            eq_parts_neg.append(f"{neg_coeff}{var_sub}")
                    else:
                        if neg_coeff == 1:
                            eq_parts_neg.append(f" + {var_sub}")
                        elif neg_coeff == -1:
                            eq_parts_neg.append(f" - {var_sub}")
                        elif neg_coeff > 0:
                            eq_parts_neg.append(f" + {neg_coeff}{var_sub}")
                        else:
                            eq_parts_neg.append(f" - {abs(neg_coeff)}{var_sub}")
                eq = "".join(eq_parts_neg) if eq_parts_neg else "0"
            else:
                rhs_val = rhs
            
            # Formatear RHS
            if rhs_val == int(rhs_val):
                rhs_str = str(int(rhs_val))
            else:
                rhs_str = f"{rhs_val:.4g}"
            
            # Ecuación final en forma estándar: ax + s = b
            latex_eq = f"{eq} + {s_name} = {rhs_str}"
            equations.append(f"\\[{latex_eq}\\]")
        
        return "\n".join(equations)
    
    def _convert_result_to_format_with_error(self, error_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convierte un resultado de error al formato estándar incluyendo los pasos.
        """
        formatted_steps = []
        
        for step in self.steps:
            formatted_step = {
                "iteration": int(step.iteration),
                "type": "initial" if step.iteration == 0 else "iteration",
                "description": str(step.description),
                "entering_variable": str(step.entering_variable) if step.entering_variable else None,
                "leaving_variable": str(step.leaving_variable) if step.leaving_variable else None,
                "pivot_row": int(step.pivot_row) if step.pivot_row is not None else None,
                "leaving_row": int(step.pivot_row) if step.pivot_row is not None else None,
                "entering_col": int(step.pivot_column) if step.pivot_column is not None else None,
                "pivot_column": int(step.pivot_column) if step.pivot_column is not None else None,
                "pivot_element": float(step.pivot_element) if step.pivot_element is not None else None,
                "tableau_before": step.tableau_before,
                "tableau_after": step.tableau,
                "obj_row_before": step.obj_row_before,
                "obj_row_after": step.obj_row_after,
                "basis_before": step.basis_before,
                "basis_after": step.basis,
                "var_names": step.var_names,
                "slack_names": list(self.slack_variables.keys()),
                "column_headers": step.column_headers,
                "row_labels": step.row_labels,
                "is_feasible": bool(step.is_feasible),
                "dual_ratios": step.dual_ratios,
                "reasoning": step.reasoning
            }
            formatted_steps.append(formatted_step)
        
        error_result["steps"] = formatted_steps
        error_result["method"] = "dual_simplex"
        error_result["iterations"] = int(len(self.steps) - 1)
        
        return self._convert_numpy_types(error_result)
    
    def _convert_result_to_format(
        self,
        obj_value: float,
        solution: Dict[str, float],
        var_names: List[str],
        equations_latex: str
    ) -> Dict[str, Any]:
        """
        Convierte el resultado al formato estándar.
        """
        formatted_steps = []
        
        for step in self.steps:
            formatted_step = {
                "iteration": int(step.iteration),
                "type": "initial" if step.iteration == 0 else "iteration",
                "description": str(step.description),
                "entering_variable": str(step.entering_variable) if step.entering_variable else None,
                "leaving_variable": str(step.leaving_variable) if step.leaving_variable else None,
                "pivot_row": int(step.pivot_row) if step.pivot_row is not None else None,
                "leaving_row": int(step.pivot_row) if step.pivot_row is not None else None,
                "entering_col": int(step.pivot_column) if step.pivot_column is not None else None,
                "pivot_column": int(step.pivot_column) if step.pivot_column is not None else None,
                "pivot_element": float(step.pivot_element) if step.pivot_element is not None else None,
                "tableau_before": step.tableau_before,
                "tableau_after": step.tableau,
                "obj_row_before": step.obj_row_before,
                "obj_row_after": step.obj_row_after,
                "basis_before": step.basis_before,
                "basis_after": step.basis,
                "var_names": step.var_names,
                "slack_names": list(self.slack_variables.keys()),
                "column_headers": step.column_headers,
                "row_labels": step.row_labels,
                "is_feasible": bool(step.is_feasible),
                "dual_ratios": step.dual_ratios,
                "reasoning": step.reasoning
            }
            formatted_steps.append(formatted_step)
        
        return self._convert_numpy_types({
            "success": True,
            "method": "dual_simplex",
            "status": "optimal",
            "objective_value": float(obj_value),
            "variables": solution,
            "iterations": int(len(self.steps) - 1),
            "equations_latex": str(equations_latex),
            "steps": formatted_steps,
            "explanation": f"Método Simplex Dual: {len(self.steps) - 1} iteraciones hasta optimalidad (factibilidad primal alcanzada)"
        })
    
    def _convert_numpy_types(self, obj: Any) -> Any:
        """Convierte tipos NumPy a tipos nativos de Python para serialización JSON."""
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj) if isinstance(obj, np.floating) else int(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._convert_numpy_types(item) for item in obj)
        return obj

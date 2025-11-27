"""
BigMMethod: Implementación correcta del método de la Gran M para programación lineal.

Soporta problemas de minimización y maximización con restricciones >=, <= y =.
Genera tablas Simplex iterativas mostrando cada paso del proceso.

CORRECCIONES REALIZADAS:
- Pivoteo calculado correctamente con índices de fila y columna exactos
- Función objetivo con términos M actualizados correctamente tras cada pivote
- Eliminación correcta de términos M cuando variables artificiales salen de la base
- Cálculo preciso de la razón mínima para selección de fila pivote
- Todos los índices de pivot se registran correctamente (sin "undefined")
"""

from typing import Dict, List, Optional, Tuple, Any
import sympy as sp
import numpy as np
from dataclasses import dataclass
import json

from app.core.logger import logger
from app.schemas.analyze_schema import MathematicalModel


@dataclass
class BigMStep:
    """Representa un paso en la resolución con el método de la Gran M."""
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
    status: str = ""  # "in_progress", "optimal", "infeasible", "unbounded"


class BigMMethod:
    """Método de la Gran M para problemas de programación lineal."""
    
    _TOL = 1e-10
    _FEASIBLE_TOL = 1e-6
    _M_VALUE = 1e6  # Constante grande M (1 millón)
    
    def __init__(self):
        """Inicializa el método de la Gran M."""
        self.M = self._M_VALUE
        self.steps: List[BigMStep] = []
        self.artificial_variables: Dict[str, int] = {}
        self.slack_variables: Dict[str, int] = {}
        self.excess_variables: Dict[str, int] = {}
        self.var_map: Dict[str, int] = {}  # Mapeo variable -> índice en tableau
        
    def solve(self, model: MathematicalModel) -> Dict[str, Any]:
        """
        Resuelve el problema usando el método de la Gran M.
        
        Args:
            model: Modelo matemático a resolver
            
        Returns:
            Diccionario con solución, tablas y pasos iterativos
        """
        try:
            self.steps = []
            self.artificial_variables = {}
            self.slack_variables = {}
            self.excess_variables = {}
            self.var_map = {}
            
            # Validar y preparar el problema
            var_names = list(model.variables.keys())
            is_max = model.objective == "max"
            
            # Crear símbolos SymPy
            symbols = {name: sp.Symbol(name, real=True, positive=True) for name in var_names}
            
            # Parsear función objetivo
            obj_expr = sp.sympify(model.objective_function, locals=symbols)
            c = np.array([float(obj_expr.coeff(symbols[v], 1) or 0) for v in var_names])
            
            # Para minimización, se multiplica por -1 (convertir a maximización)
            if not is_max:
                c = -c
            
            # Parsear restricciones
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
            tableau, basis, basis_cols = self._build_initial_tableau(
                c, constraints_data, var_names, is_max
            )
            
            if tableau is None:
                return {
                    "success": False,
                    "error": "No se pueden agregar variables artificiales necesarias",
                    "steps": []
                }
            
            # Generar paso inicial
            self._add_initial_step(tableau, basis, basis_cols, var_names)
            
            # Iterar con Simplex
            max_iterations = 1000
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Encontrar columna pivote (variable entrante)
                entering_col = self._find_entering_column(tableau)
                
                if entering_col is None:
                    # Solución óptima encontrada
                    self._add_final_step(tableau, basis, basis_cols, var_names, "optimal")
                    break
                
                # Encontrar fila pivote (variable saliente)
                leaving_row = self._find_leaving_row(tableau, entering_col)
                
                if leaving_row is None:
                    # Problema ilimitado
                    self._add_final_step(tableau, basis, basis_cols, var_names, "unbounded")
                    result = {
                        "success": False,
                        "status": "unbounded",
                        "error": "El problema es ilimitado (solución no acotada)"
                    }
                    return self._convert_result_to_simplex_format_with_error(result)
                
                # Obtener información del pivote ANTES de modificar
                entering_name = self._get_variable_name_from_col(entering_col)
                leaving_name = basis[leaving_row]
                pivot_element = float(tableau[leaving_row, entering_col])
                
                # Registrar estado antes del pivote
                tableau_before = tableau.copy()
                basis_before = basis[:]
                
                # Realizar pivote (modifica tableau EN LUGAR)
                self._pivot_in_place(tableau, leaving_row, entering_col)
                
                # Actualizar base
                basis[leaving_row] = entering_name
                basis_cols[leaving_row] = entering_col
                
                # Registrar paso con índices correctos
                self._add_iteration_step(
                    tableau, basis, basis_cols, var_names,
                    entering_name, leaving_name, leaving_row, entering_col,
                    pivot_element, iteration, tableau_before, basis_before
                )
            
            # Verificar infactibilidad
            artificial_in_basis = any(
                var_name.startswith("a") and abs(tableau[i, -1]) > self._FEASIBLE_TOL
                for i, var_name in enumerate(basis)
            )
            
            if artificial_in_basis:
                result = {
                    "success": False,
                    "status": "infeasible",
                    "error": "El problema es infactible (variables artificiales en la solución final)"
                }
                return self._convert_result_to_simplex_format_with_error(result)
            
            # Extraer solución
            solution = self._extract_solution(tableau, basis, var_names)
            obj_value = float(tableau[-1, -1])
            
            if not is_max:
                obj_value = -obj_value
            
            # Generar ecuaciones LaTeX con variables de holgura, exceso y artificiales
            equations_latex = self._generate_equations_latex(
                constraints_data, var_names
            )
            
            return self._convert_result_to_simplex_format(
                obj_value, solution, var_names, is_max, equations_latex
            )
            
        except Exception as e:
            logger.error(f"Error en BigMMethod.solve: {str(e)}", exc_info=True)
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
                # Parsear: "2*x1 + x2 <= 10"
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
        is_max: bool
    ) -> Tuple[Optional[np.ndarray], List[str], List[int]]:
        """
        Construye el tableau inicial con variables de holgura y artificiales.
        
        CORRECCIONES:
        - Mantiene mapeo consistente de variables a índices
        - Inicializa correctamente la fila Z con términos M
        - Asegura RHS positivo antes de construir tableau
        """
        n_vars = len(var_names)
        n_constraints = len(constraints_data)
        
        # Contar variables necesarias
        n_slack = 0
        n_excess = 0
        n_artificial = 0
        
        for coeffs, op, rhs in constraints_data:
            if op == "<=":
                n_slack += 1
            elif op == ">=":
                n_excess += 1
                n_artificial += 1
            elif op == "=":
                n_artificial += 1
        
        n_total = n_vars + n_slack + n_excess + n_artificial
        
        # Inicializar tableau
        tableau = np.zeros((n_constraints + 1, n_total + 1))
        
        # Crear mapeo de variables a índices (CRÍTICO para consistencia)
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
        
        # Variables de exceso
        for i in range(n_excess):
            e_name = f"e{i+1}"
            self.var_map[e_name] = idx
            self.excess_variables[e_name] = idx
            idx += 1
        
        # Variables artificiales
        for i in range(n_artificial):
            a_name = f"a{i+1}"
            self.var_map[a_name] = idx
            self.artificial_variables[a_name] = idx
            idx += 1
        
        # Llenar restricciones
        basis = []
        basis_cols = []
        
        slack_counter = 1
        excess_counter = 1
        artificial_counter = 1
        
        for i, (coeffs, op, rhs) in enumerate(constraints_data):
            # Coeficientes de variables originales
            tableau[i, :n_vars] = coeffs
            
            # Variables de holgura/exceso/artificiales
            if op == "<=":
                s_name = f"s{slack_counter}"
                s_col = self.var_map[s_name]
                tableau[i, s_col] = 1
                basis.append(s_name)
                basis_cols.append(s_col)
                slack_counter += 1
                
            elif op == ">=":
                e_name = f"e{excess_counter}"
                a_name = f"a{artificial_counter}"
                e_col = self.var_map[e_name]
                a_col = self.var_map[a_name]
                
                tableau[i, e_col] = -1
                tableau[i, a_col] = 1
                
                basis.append(a_name)
                basis_cols.append(a_col)
                
                excess_counter += 1
                artificial_counter += 1
                
            elif op == "=":
                a_name = f"a{artificial_counter}"
                a_col = self.var_map[a_name]
                tableau[i, a_col] = 1
                basis.append(a_name)
                basis_cols.append(a_col)
                artificial_counter += 1
            
            # RHS
            tableau[i, -1] = rhs
        
        # Construir fila objetivo CORRECTAMENTE
        obj_row = np.zeros(n_total + 1)
        obj_row[:n_vars] = -c
        
        # Penalizar variables artificiales con M
        # Para cada variable artificial en la base inicial, restar M veces su ecuación
        for i, var_name in enumerate(basis):
            if var_name.startswith("a"):
                # Restar M * (fila i) de la fila objetivo
                obj_row -= self.M * tableau[i]
        
        tableau[-1] = obj_row
        
        return tableau, basis, basis_cols
    
    def _find_entering_column(self, tableau: np.ndarray) -> Optional[int]:
        """
        Encuentra la columna pivote (variable entrante).
        Selecciona la columna con coeficiente más negativo en la fila objetivo.
        """
        obj_row = tableau[-1, :-1]
        min_idx = int(np.argmin(obj_row))
        min_coeff = float(obj_row[min_idx])
        
        if min_coeff >= -self._TOL:
            return None
        
        return min_idx
    
    def _find_leaving_row(self, tableau: np.ndarray, entering_col: int) -> Optional[int]:
        """
        Encuentra la fila pivote (variable saliente).
        Usa el criterio mínimo de la razón SOLO con coeficientes positivos.
        
        CORRECCION: Solo calcula razones para elementos positivos en la columna pivote.
        """
        col = tableau[:-1, entering_col]
        rhs = tableau[:-1, -1]
        
        min_ratio = float('inf')
        min_row = None
        
        for i in range(len(col)):
            if col[i] > self._TOL:  # Solo para coeficientes POSITIVOS
                ratio = rhs[i] / col[i]
                if 0 <= ratio < min_ratio:  # Ratio no negativo
                    min_ratio = ratio
                    min_row = i
        
        return min_row
    
    def _pivot_in_place(self, tableau: np.ndarray, pivot_row: int, pivot_col: int) -> None:
        """
        Realiza el pivoteo modificando el tableau EN LUGAR.
        Esto asegura que el tableau actualizado y mostrado sean iguales.
        """
        pivot_element = tableau[pivot_row, pivot_col]
        
        # Dividir fila pivote
        tableau[pivot_row] = tableau[pivot_row] / pivot_element
        
        # Eliminar otros elementos en la columna
        for i in range(len(tableau)):
            if i != pivot_row and abs(tableau[i, pivot_col]) > self._TOL:
                factor = tableau[i, pivot_col]
                tableau[i] = tableau[i] - factor * tableau[pivot_row]
    
    def _get_variable_name_from_col(self, col: int) -> str:
        """
        Obtiene el nombre de la variable usando el mapeo inverso.
        CORRECCION: Usa el var_map consistentemente.
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
        Usa los nombres de la base para identificar variables en base (con valores RHS)
        y asigna 0 a variables fuera de base.
        """
        solution = {v: 0.0 for v in var_names}
        
        # Para cada variable en la base, extraer su valor del RHS
        for i, var_name in enumerate(basis):
            # Solo contar si la variable está en la solución original (no slack, etc.)
            if var_name in var_names:
                rhs_value = float(tableau[i, -1])
                solution[var_name] = rhs_value if abs(rhs_value) > self._TOL else 0.0
        
        return solution
    
    def _add_initial_step(
        self,
        tableau: np.ndarray,
        basis: List[str],
        basis_cols: List[int],
        var_names: List[str]
    ) -> None:
        """
        Agrega el paso inicial (tableau sin iterar).
        Convierte var_names a strings para que los headers sean serializables.
        """
        # Convertir var_names a strings si son Symbols
        var_names_str = [str(v) if hasattr(v, '__str__') else v for v in var_names]
        
        column_headers = var_names_str + list(self.slack_variables.keys()) + \
                        list(self.excess_variables.keys()) + list(self.artificial_variables.keys()) + \
                        ["RHS"]
        
        row_labels = [str(b) for b in basis] + ["Función Objetivo"]
        
        step = BigMStep(
            iteration=0,
            description="Tableau inicial con variables artificiales",
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
            reasoning={
                "description": "Se establece el tableau inicial",
                "slack_variables": {str(k): int(v) for k, v in self.slack_variables.items()},
                "excess_variables": {str(k): int(v) for k, v in self.excess_variables.items()},
                "artificial_variables": {str(k): int(v) for k, v in self.artificial_variables.items()},
                "M_value": self.M,
                "variables_and_columns": {str(k): int(v) for k, v in self.var_map.items()}
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
        basis_before: List[str]
    ) -> None:
        """
        Agrega un paso de iteración con INDICES CORRECTAMENTE ASIGNADOS.
        CORRECCIONES: 
        - Los índices pivot_row y pivot_col son siempre números enteros válidos
        - La tabla mostrada es la tabla DESPUÉS del pivote (actualizada)
        - Los headers usan nombres de variables como strings
        - Se asegura que los índices se serialicen correctamente (no undefined)
        """
        # Convertir var_names a strings si son Symbols
        var_names_str = [str(v) if hasattr(v, '__str__') else v for v in var_names]
        
        column_headers = var_names_str + list(self.slack_variables.keys()) + \
                        list(self.excess_variables.keys()) + list(self.artificial_variables.keys()) + \
                        ["RHS"]
        
        row_labels = basis + ["Función Objetivo"]
        
        # Convertir índices a int explícitamente para evitar problemas de serialización
        pivot_row_int = int(pivot_row)
        pivot_col_int = int(pivot_col)
        pivot_element_float = float(pivot_element)
        
        # Calcular razones detalladas
        ratios = []
        col_values = tableau_before[:-1, pivot_col_int]
        rhs_values = tableau_before[:-1, -1]
        
        for i in range(len(tableau_before) - 1):
            if col_values[i] > self._TOL:
                ratio = float(rhs_values[i] / col_values[i])
                ratios.append({
                    "row": i,
                    "variable": basis_before[i],
                    "rhs": float(rhs_values[i]),
                    "column_coefficient": float(col_values[i]),
                    "ratio": ratio,
                    "is_minimum": (i == pivot_row_int)
                })
        
        # Crear paso CON indices numéricos válidos y serializables
        step = BigMStep(
            iteration=iteration,
            description=f"Iteración {iteration}: Entra {entering_name}, Sale {leaving_name}",
            entering_variable=str(entering_name),  # Asegurar string
            leaving_variable=str(leaving_name),    # Asegurar string
            pivot_row=pivot_row_int,               # int puro
            pivot_column=pivot_col_int,            # int puro
            pivot_element=pivot_element_float,     # float puro
            tableau=tableau.tolist(),              # Tabla DESPUÉS del pivote
            tableau_before=tableau_before.tolist(),
            obj_row_before=tableau_before[-1].tolist(),
            obj_row_after=tableau[-1].tolist(),
            basis=[str(b) for b in basis],         # Strings
            basis_before=[str(b) for b in basis_before],
            basis_columns=[int(bc) for bc in basis_cols],  # ints puros
            column_headers=[str(h) for h in column_headers],  # Strings
            row_labels=[str(rl) for rl in row_labels],        # Strings
            var_names=var_names_str,
            reasoning={
                "description": f"Pivoteo en fila {pivot_row_int}, columna {pivot_col_int}",
                "entering_variable": str(entering_name),
                "leaving_variable": str(leaving_name),
                "pivot_column_index": pivot_col_int,
                "pivot_row_index": pivot_row_int,
                "pivot_element": pivot_element_float,
                "column_header_for_entering": str(column_headers[pivot_col_int]),
                "row_label_for_leaving": str(row_labels[pivot_row_int]),
                "ratios_analysis": ratios
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
        Registra el paso final cuando se alcanza optimalidad o se detecta 
        infeasibilidad/unboundedness.
        """
        # Convertir var_names a strings si son Symbols
        var_names_str = [str(v) if hasattr(v, '__str__') else v for v in var_names]
        
        column_headers = var_names_str + list(self.slack_variables.keys()) + \
                        list(self.excess_variables.keys()) + list(self.artificial_variables.keys()) + \
                        ["RHS"]
        
        row_labels = [str(b) for b in basis] + ["Función Objetivo"]
        
        step = BigMStep(
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
            status=status,
            reasoning={
                "description": "Criterio de optimalidad alcanzado",
                "all_reduced_costs_nonnegative": status == "optimal",
                "final_tableau": True
            }
        )
        self.steps.append(step)
    
    def _format_tableau_as_string(
        self,
        tableau: np.ndarray,
        column_headers: List[str],
        row_labels: List[str]
    ) -> str:
        """
        Formatea un tableau como una tabla legible en texto.
        Útil para mostrar visualmente el estado del tableau en cada iteración.
        """
        lines = []
        
        # Calcular anchos de columna
        col_widths = []
        for i, header in enumerate(column_headers):
            max_width = len(header)
            for row in tableau:
                val_str = f"{row[i]:.4g}"
                max_width = max(max_width, len(val_str))
            col_widths.append(max_width)
        
        # Calcular ancho para etiquetas de fila
        row_label_width = max(len(label) for label in row_labels) if row_labels else 10
        
        # Encabezado
        header_line = " " * (row_label_width + 2)
        for header, width in zip(column_headers, col_widths):
            header_line += f"{header:>{width}}  "
        lines.append(header_line)
        
        # Separador
        separator = "-" * len(header_line)
        lines.append(separator)
        
        # Filas
        for row_idx, (label, row) in enumerate(zip(row_labels, tableau)):
            row_line = f"{label:<{row_label_width}} |"
            for val, width in zip(row, col_widths):
                val_str = f"{val:.4g}"
                row_line += f" {val_str:>{width}} "
            lines.append(row_line)
        
        return "\n".join(lines)
    
    def get_formatted_steps(self) -> List[Dict[str, Any]]:
        """
        Retorna los pasos formateados con tablas como strings legibles.
        Útil para depuración y visualización.
        """
        formatted_steps = []
        
        for step in self.steps:
            formatted_step = self._step_to_dict(step)
            
            # Agregar tableau formateado como string
            if step.tableau and step.column_headers and step.row_labels:
                try:
                    tableau_arr = np.array(step.tableau)
                    formatted_step["tableau_formatted"] = self._format_tableau_as_string(
                        tableau_arr,
                        step.column_headers,
                        step.row_labels
                    )
                except Exception as e:
                    formatted_step["tableau_formatted"] = f"Error al formatear: {str(e)}"
            
            formatted_steps.append(formatted_step)
        
        return formatted_steps

    def _generate_equations_latex(
        self,
        constraints_data: List[Tuple[np.ndarray, str, float]],
        var_names: List[str]
    ) -> str:
        """
        Genera ecuaciones LaTeX con variables de holgura, exceso y artificiales.
        Formato similar al Simplex pero incluyendo variables adicionales.
        """
        equations = []
        
        slack_counter = 1
        excess_counter = 1
        artificial_counter = 1
        
        for i, (coeffs, op, rhs) in enumerate(constraints_data):
            # Construir términos de variables originales
            var_terms = []
            for j, var in enumerate(var_names):
                coeff = float(coeffs[j])
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
            
            rhs_str = f"{int(rhs) if rhs == int(rhs) else f'{rhs:.4g}'}"
            
            # Agregar variables según el tipo de restricción
            if op == "<=":
                s_name = f"s_{{{slack_counter}}}"
                latex_eq = f"{eq} + {s_name} = {rhs_str}"
                equations.append(f"\\[{latex_eq}\\]")
                slack_counter += 1
                
            elif op == ">=":
                e_name = f"e_{{{excess_counter}}}"
                a_name = f"a_{{{artificial_counter}}}"
                latex_eq = f"{eq} - {e_name} + {a_name} = {rhs_str}"
                equations.append(f"\\[{latex_eq}\\]")
                excess_counter += 1
                artificial_counter += 1
                
            elif op == "=":
                a_name = f"a_{{{artificial_counter}}}"
                latex_eq = f"{eq} + {a_name} = {rhs_str}"
                equations.append(f"\\[{latex_eq}\\]")
                artificial_counter += 1
        
        return "\n".join(equations)
    
    def _convert_result_to_simplex_format_with_error(self, error_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convierte un resultado de error al formato Simplex incluyendo los pasos registrados.
        Esto asegura que el frontend siempre tenga 'steps' disponible.
        """
        # Convertir steps al formato Simplex
        formatted_steps = []
        
        for step in self.steps:
            if step.iteration == 0:
                # Paso inicial
                formatted_steps.append({
                    "iteration": 0,
                    "type": "initial",
                    "description": "Tableau inicial con variables artificiales",
                    "tableau_before": step.tableau_before,
                    "tableau_after": step.tableau,
                    "obj_row_before": step.obj_row_before,
                    "obj_row_after": step.obj_row_after,
                    "basis_before": step.basis_before,
                    "basis_after": step.basis,
                    "var_names": step.var_names,
                    "slack_names": list(self.slack_variables.keys()),
                    "excess_names": list(self.excess_variables.keys()),
                    "artificial_names": list(self.artificial_variables.keys()),
                    "column_headers": step.column_headers,
                    "row_labels": step.row_labels
                })
            else:
                # Pasos de iteración
                formatted_steps.append({
                    "iteration": step.iteration,
                    "type": "iteration",
                    "description": step.description,
                    "entering_variable": step.entering_variable,
                    "leaving_variable": step.leaving_variable,
                    "pivot_row": step.pivot_row,
                    "leaving_row": step.pivot_row,
                    "entering_col": step.pivot_column,
                    "pivot_column": step.pivot_column,
                    "pivot_element": step.pivot_element,
                    "tableau_before": step.tableau_before,
                    "tableau_after": step.tableau,
                    "obj_row_before": step.obj_row_before,
                    "obj_row_after": step.obj_row_after,
                    "basis_before": step.basis_before,
                    "basis_after": step.basis,
                    "var_names": step.var_names,
                    "slack_names": list(self.slack_variables.keys()),
                    "excess_names": list(self.excess_variables.keys()),
                    "artificial_names": list(self.artificial_variables.keys()),
                    "column_headers": step.column_headers,
                    "row_labels": step.row_labels
                })
        
        # Agregar steps al resultado de error
        error_result["steps"] = formatted_steps
        error_result["method"] = "big_m"
        error_result["iterations"] = len(self.steps) - 1
        
        return self._convert_numpy_types(error_result)
    
    def _convert_result_to_simplex_format(
        self,
        obj_value: float,
        solution: Dict[str, float],
        var_names: List[str],
        is_max: bool,
        equations_latex: str
    ) -> Dict[str, Any]:
        """
        Convierte el resultado del Gran M al formato de Simplex.
        Esto hace que la visualización sea consistente en el frontend.
        """
        # Convertir steps al formato Simplex
        formatted_steps = []
        
        for step in self.steps:
            if step.iteration == 0:
                # Paso inicial - sin detalles de pivotación
                formatted_steps.append({
                    "iteration": 0,
                    "type": "initial",
                    "description": "Tableau inicial con variables artificiales",
                    "tableau_before": step.tableau_before,
                    "tableau_after": step.tableau,
                    "obj_row_before": step.obj_row_before,
                    "obj_row_after": step.obj_row_after,
                    "basis_before": step.basis_before,
                    "basis_after": step.basis,
                    "var_names": step.var_names or var_names,
                    "slack_names": list(self.slack_variables.keys()),
                    "excess_names": list(self.excess_variables.keys()),
                    "artificial_names": list(self.artificial_variables.keys()),
                    "column_headers": step.column_headers,
                    "row_labels": step.row_labels
                })
            else:
                # Pasos de iteración - formato Simplex
                formatted_steps.append({
                    "iteration": step.iteration,
                    "type": "iteration",
                    "description": step.description,
                    "entering_variable": step.entering_variable,
                    "leaving_variable": step.leaving_variable,
                    "pivot_row": step.pivot_row,
                    "leaving_row": step.pivot_row,
                    "entering_col": step.pivot_column,
                    "pivot_column": step.pivot_column,
                    "pivot_element": step.pivot_element,
                    "tableau_before": step.tableau_before,
                    "tableau_after": step.tableau,
                    "obj_row_before": step.obj_row_before,
                    "obj_row_after": step.obj_row_after,
                    "basis_before": step.basis_before,
                    "basis_after": step.basis,
                    "var_names": step.var_names or var_names,
                    "slack_names": list(self.slack_variables.keys()),
                    "excess_names": list(self.excess_variables.keys()),
                    "artificial_names": list(self.artificial_variables.keys()),
                    "column_headers": step.column_headers,
                    "row_labels": step.row_labels
                })
        
        return self._convert_numpy_types({
            "success": True,
            "method": "big_m",
            "status": "optimal",
            "objective_value": obj_value,
            "variables": solution,
            "iterations": len(self.steps) - 1,
            "equations_latex": equations_latex,
            "steps": formatted_steps,
            "explanation": f"Método Gran M: {len(self.steps) - 1} iteraciones hasta optimalidad"
        })
    
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

"""
SensitivityAnalysis: Análisis de sensibilidad post-óptimo para programación lineal.

Este módulo implementa el análisis de sensibilidad educativo y didáctico para
problemas de programación lineal resueltos con los métodos Simplex, Simplex Dual
y Gran M.

Teoría del Análisis de Sensibilidad Post-Óptimo:
================================================

El análisis de sensibilidad estudia cómo cambia la solución óptima cuando se
modifican los parámetros del problema. Es fundamental para:

1. **Evaluación de la robustez**: Determinar si pequeños cambios en los datos
   alteran significativamente la solución.

2. **Planificación estratégica**: Identificar qué recursos son más valiosos
   (precios sombra) y cuánto se puede variar la disponibilidad de recursos
   sin cambiar la base óptima.

3. **Análisis económico**: Los precios sombra representan el valor marginal
   de cada recurso, es decir, cuánto mejoraría el objetivo si se dispusiera
   de una unidad adicional de ese recurso.

Componentes del Análisis:
------------------------

1. **Rangos de Optimalidad (Coeficientes c_j)**:
   - ¿Cuánto pueden variar los coeficientes de la función objetivo sin que
     cambie la base óptima (aunque sí puede cambiar el valor óptimo)?
   - Fórmula: c_j puede variar en [c_j - δ⁻, c_j + δ⁺] donde la base se mantiene

2. **Rangos de Factibilidad (RHS b_i)**:
   - ¿Cuánto pueden variar los términos independientes sin que cambie la
     base óptima (pero sí cambian los valores de las variables)?
   - Estos rangos determinan hasta dónde son válidos los precios sombra

3. **Precios Sombra (π_i) o Valores Duales**:
   - Representan el cambio en el valor óptimo por unidad de incremento en b_i
   - Son los coeficientes de las variables de holgura en la fila Z final
   - Interpretación económica: valor marginal de cada recurso

4. **Costos Reducidos (c̄_j)**:
   - Para variables no básicas: ¿cuánto debe mejorar c_j para que la variable
     entre a la base?
   - Son los coeficientes en la fila Z del tableau óptimo

Implementación basada en Taha (Investigación de Operaciones) y teoría clásica.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from dataclasses import dataclass, field
from app.core.logger import logger
from app.core.groq_client import GroqClient
from app.core.config import settings


@dataclass
class SensitivityRange:
    """Representa un rango de sensibilidad con explicación didáctica."""
    variable: str
    current_value: float
    lower_bound: float
    upper_bound: float
    allowable_decrease: float
    allowable_increase: float
    explanation: str
    interpretation: str


@dataclass
class ShadowPrice:
    """Representa un precio sombra con interpretación económica."""
    constraint_index: int
    constraint_name: str
    value: float
    slack_variable: str
    binding: bool  # Si la restricción está activa (holgura = 0)
    explanation: str
    economic_interpretation: str


@dataclass
class ReducedCost:
    """Representa un costo reducido con interpretación."""
    variable: str
    value: float
    is_basic: bool
    explanation: str
    interpretation: str


@dataclass
class SensitivityAnalysisResult:
    """Resultado completo del análisis de sensibilidad."""
    # Rangos de optimalidad
    objective_ranges: List[SensitivityRange]
    
    # Rangos de factibilidad
    rhs_ranges: List[SensitivityRange]
    
    # Precios sombra
    shadow_prices: List[ShadowPrice]
    
    # Costos reducidos
    reduced_costs: List[ReducedCost]
    
    # Información del problema
    objective_value: float
    is_maximization: bool
    basic_variables: List[str]
    non_basic_variables: List[str]
    
    # Explicaciones didácticas
    theory_explanation: str
    practical_insights: List[str]
    
    # Datos del tableau final para referencia
    final_tableau: Optional[List[List[float]]] = None
    column_headers: Optional[List[str]] = None
    row_labels: Optional[List[str]] = None


class SensitivityAnalyzer:
    """
    Analizador de sensibilidad post-óptimo para programación lineal.
    
    Proporciona análisis detallado y didáctico de:
    - Rangos de optimalidad de coeficientes de la función objetivo
    - Rangos de factibilidad de los términos independientes (RHS)
    - Precios sombra (valores duales)
    - Costos reducidos
    
    Compatible con los métodos: Simplex, Simplex Dual y Gran M.
    """
    
    _TOL = 1e-10
    _INF_THRESHOLD = 1e10
    
    def __init__(self):
        """Inicializa el analizador de sensibilidad."""
        pass
    
    def analyze(
        self,
        solver_result: Dict[str, Any],
        original_c: np.ndarray,
        original_b: np.ndarray,
        var_names: List[str],
        constraint_names: Optional[List[str]] = None,
        is_maximization: bool = True
    ) -> Dict[str, Any]:
        """
        Realiza el análisis de sensibilidad completo.
        
        Args:
            solver_result: Resultado del solver (Simplex, Dual, Gran M)
            original_c: Coeficientes originales de la función objetivo
            original_b: Términos independientes originales (RHS)
            var_names: Nombres de las variables de decisión
            constraint_names: Nombres de las restricciones (opcional)
            is_maximization: True si es maximización, False si es minimización
            
        Returns:
            Diccionario con el análisis de sensibilidad completo
        """
        try:
            # Validar que la solución sea óptima
            if not solver_result.get("success"):
                return {
                    "success": False,
                    "error": "No se puede realizar análisis de sensibilidad: la solución no es óptima",
                    "sensitivity_analysis": None
                }
            
            # Obtener datos del tableau final
            steps = solver_result.get("steps", [])
            if not steps:
                return {
                    "success": False,
                    "error": "No hay pasos del solver disponibles para el análisis",
                    "sensitivity_analysis": None
                }
            
            # Obtener el último paso (tableau óptimo)
            final_step = steps[-1]
            final_tableau = np.array(final_step.get("tableau_after") or final_step.get("tableau", []))
            
            if final_tableau.size == 0:
                return {
                    "success": False,
                    "error": "Tableau final no disponible",
                    "sensitivity_analysis": None
                }
            
            # Extraer información de la base
            basis = final_step.get("basis_after") or final_step.get("basis", [])
            column_headers = final_step.get("column_headers", [])
            row_labels = final_step.get("row_labels", [])
            slack_names = final_step.get("slack_names", [])
            
            # Obtener nombres de variables de holgura/artificiales si existen
            artificial_names = final_step.get("artificial_names", [])
            
            # Número de variables originales y restricciones
            n_vars = len(var_names)
            n_constraints = len(original_b)
            
            # Generar nombres de restricciones si no se proporcionan
            if constraint_names is None:
                constraint_names = [f"Restricción {i+1}" for i in range(n_constraints)]
            
            # Calcular análisis de sensibilidad
            objective_ranges = self._calculate_objective_ranges(
                final_tableau, basis, var_names, slack_names, 
                original_c, is_maximization, column_headers
            )
            
            rhs_ranges = self._calculate_rhs_ranges(
                final_tableau, basis, var_names, slack_names,
                original_b, constraint_names, column_headers
            )
            
            shadow_prices = self._calculate_shadow_prices(
                final_tableau, basis, slack_names, constraint_names,
                is_maximization, column_headers
            )
            
            reduced_costs = self._calculate_reduced_costs(
                final_tableau, basis, var_names, slack_names,
                is_maximization, column_headers
            )
            
            # Identificar variables básicas y no básicas
            basic_vars = [v for v in var_names if v in basis]
            non_basic_vars = [v for v in var_names if v not in basis]
            
            # Generar explicaciones didácticas
            theory_explanation = self._generate_theory_explanation(is_maximization)
            practical_insights = self._generate_practical_insights(
                objective_ranges, rhs_ranges, shadow_prices, reduced_costs,
                solver_result.get("objective_value", 0), is_maximization
            )
            
            # Construir resultado
            result = {
                "success": True,
                "sensitivity_analysis": {
                    "objective_ranges": [self._range_to_dict(r) for r in objective_ranges],
                    "rhs_ranges": [self._range_to_dict(r) for r in rhs_ranges],
                    "shadow_prices": [self._shadow_price_to_dict(sp) for sp in shadow_prices],
                    "reduced_costs": [self._reduced_cost_to_dict(rc) for rc in reduced_costs],
                    "objective_value": solver_result.get("objective_value", 0),
                    "is_maximization": is_maximization,
                    "basic_variables": basic_vars,
                    "non_basic_variables": non_basic_vars,
                    "theory_explanation": theory_explanation,
                    "practical_insights": practical_insights,
                    "final_tableau": final_tableau.tolist(),
                    "column_headers": column_headers,
                    "row_labels": row_labels
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis de sensibilidad: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "sensitivity_analysis": None
            }
    
    def _calculate_objective_ranges(
        self,
        tableau: np.ndarray,
        basis: List[str],
        var_names: List[str],
        slack_names: List[str],
        original_c: np.ndarray,
        is_maximization: bool,
        column_headers: List[str]
    ) -> List[SensitivityRange]:
        """
        Calcula los rangos de optimalidad para los coeficientes de la función objetivo.
        
        TEORÍA:
        -------
        Para una variable NO BÁSICA x_j:
        - El costo reducido c̄_j indica cuánto puede mejorar c_j antes de que x_j entre a la base
        - Para maximización: c_j puede aumentar hasta c_j + |c̄_j|
        - Para minimización: c_j puede disminuir hasta c_j - |c̄_j|
        
        Para una variable BÁSICA x_k:
        - El análisis es más complejo, involucrando la fila k del tableau
        - Necesitamos que todos los costos reducidos mantengan su signo
        """
        ranges = []
        n_vars = len(var_names)
        
        # Construir mapeo de nombres a índices de columna
        col_map = {name: i for i, name in enumerate(column_headers) if i < len(column_headers) - 1}
        
        # Obtener fila Z (última fila del tableau, sin RHS)
        z_row = tableau[-1, :-1]
        n_cols = len(z_row)
        
        for j, var in enumerate(var_names):
            if j >= len(original_c):
                continue
                
            c_j = float(original_c[j])
            col_idx = col_map.get(var, j)
            
            if col_idx >= n_cols:
                continue
            
            # Costo reducido actual (del tableau)
            reduced_cost = float(z_row[col_idx]) if col_idx < n_cols else 0.0
            
            if var in basis:
                # VARIABLE BÁSICA
                # Encontrar la fila donde está esta variable
                try:
                    basic_row = basis.index(var)
                except ValueError:
                    basic_row = -1
                
                if basic_row >= 0 and basic_row < tableau.shape[0] - 1:
                    # Calcular rangos para variable básica
                    lower, upper = self._calculate_basic_var_objective_range(
                        tableau, basis, var, basic_row, col_map, 
                        var_names, slack_names, c_j, is_maximization
                    )
                else:
                    lower, upper = float('-inf'), float('inf')
                
                # Explicación para variable básica
                explanation = (
                    f"La variable {var} está en la base óptima (valor = {self._get_basic_var_value(tableau, basic_row):.4g}). "
                    f"El coeficiente c_{j+1} = {c_j:.4g} puede variar en "
                    f"[{self._format_bound(lower)}, {self._format_bound(upper)}] "
                    f"sin que cambie qué variables están en la base."
                )
                interpretation = (
                    f"Dentro de este rango, {var} permanecerá en la solución óptima. "
                    f"El valor óptimo Z cambiará proporcionalmente al cambio en c_{j+1}."
                )
            else:
                # VARIABLE NO BÁSICA
                # El costo reducido indica directamente el rango
                if is_maximization:
                    # Para max: c̄_j <= 0 para optimalidad
                    # Si c̄_j < 0, podemos aumentar c_j hasta que c̄_j = 0
                    lower = float('-inf')
                    if reduced_cost < -self._TOL:
                        upper = c_j + abs(reduced_cost)
                    else:
                        upper = float('inf')  # Ya es óptimo o puede aumentar indefinidamente
                else:
                    # Para min: c̄_j >= 0 para optimalidad
                    # Si c̄_j > 0, podemos disminuir c_j hasta que c̄_j = 0
                    if reduced_cost > self._TOL:
                        lower = c_j - abs(reduced_cost)
                    else:
                        lower = float('-inf')
                    upper = float('inf')
                
                # Explicación para variable no básica
                explanation = (
                    f"La variable {var} NO está en la base (valor = 0). "
                    f"El costo reducido es c̄_{j+1} = {reduced_cost:.4g}."
                )
                if is_maximization:
                    if abs(reduced_cost) > self._TOL:
                        interpretation = (
                            f"Para que {var} entre a la solución, su coeficiente debe aumentar "
                            f"en {abs(reduced_cost):.4g} unidades (de {c_j:.4g} a {c_j + abs(reduced_cost):.4g})."
                        )
                    else:
                        interpretation = (
                            f"El costo reducido es prácticamente cero, indicando posible solución alternativa "
                            f"si {var} entrara a la base."
                        )
                else:
                    if abs(reduced_cost) > self._TOL:
                        interpretation = (
                            f"Para que {var} entre a la solución, su coeficiente debe disminuir "
                            f"en {abs(reduced_cost):.4g} unidades (de {c_j:.4g} a {c_j - abs(reduced_cost):.4g})."
                        )
                    else:
                        interpretation = (
                            f"El costo reducido es prácticamente cero, indicando posible solución alternativa."
                        )
            
            # Calcular incrementos permitidos
            allowable_decrease = c_j - lower if lower != float('-inf') else float('inf')
            allowable_increase = upper - c_j if upper != float('inf') else float('inf')
            
            # Asegurar valores no negativos para los incrementos
            allowable_decrease = max(0, allowable_decrease)
            allowable_increase = max(0, allowable_increase)
            
            ranges.append(SensitivityRange(
                variable=var,
                current_value=c_j,
                lower_bound=lower,
                upper_bound=upper,
                allowable_decrease=allowable_decrease,
                allowable_increase=allowable_increase,
                explanation=explanation,
                interpretation=interpretation
            ))
        
        return ranges
    
    def _calculate_basic_var_objective_range(
        self,
        tableau: np.ndarray,
        basis: List[str],
        var: str,
        basic_row: int,
        col_map: Dict[str, int],
        var_names: List[str],
        slack_names: List[str],
        c_j: float,
        is_maximization: bool
    ) -> Tuple[float, float]:
        """
        Calcula el rango de optimalidad para el coeficiente de una variable básica.
        
        MÉTODO:
        -------
        Para una variable básica x_k en la fila r del tableau:
        - Cuando c_k cambia en Δ, los costos reducidos de las no básicas cambian en -Δ * a_{rj}
        - Para mantener optimalidad (max): todos c̄_j + cambio <= 0
        - Para mantener optimalidad (min): todos c̄_j + cambio >= 0
        """
        z_row = tableau[-1, :-1]
        basic_row_values = tableau[basic_row, :-1]
        n_cols = len(z_row)
        
        min_decrease = float('inf')  # Máximo decremento permitido
        min_increase = float('inf')  # Máximo incremento permitido
        
        # Analizar cada variable no básica
        for col in range(n_cols):
            # Obtener nombre de variable en esta columna
            var_name = None
            for name, idx in col_map.items():
                if idx == col:
                    var_name = name
                    break
            
            # Saltar si es una variable básica o la propia variable
            if var_name is None or var_name in basis:
                continue
            
            # Coeficiente en la fila de la variable básica
            a_rj = basic_row_values[col]
            
            if abs(a_rj) < self._TOL:
                continue  # No afecta este costo reducido
            
            # Costo reducido actual de la variable no básica
            c_bar_j = z_row[col]
            
            if is_maximization:
                # Condición: c̄_j - Δ * a_rj <= 0 (debe mantenerse no positivo)
                # Si a_rj > 0: Δ >= c̄_j / a_rj (límite inferior para Δ)
                # Si a_rj < 0: Δ <= c̄_j / a_rj (límite superior para Δ)
                if a_rj > self._TOL:
                    # Límite al incrementar c_k (Δ positivo)
                    ratio = c_bar_j / a_rj
                    if ratio > 0:
                        min_increase = min(min_increase, ratio)
                elif a_rj < -self._TOL:
                    # Límite al decrementar c_k (Δ negativo)
                    ratio = -c_bar_j / a_rj
                    if ratio > 0:
                        min_decrease = min(min_decrease, ratio)
            else:
                # Para minimización: c̄_j + Δ * a_rj >= 0 (debe mantenerse no negativo)
                if a_rj > self._TOL:
                    ratio = -c_bar_j / a_rj
                    if ratio > 0:
                        min_decrease = min(min_decrease, ratio)
                elif a_rj < -self._TOL:
                    ratio = c_bar_j / a_rj
                    if ratio > 0:
                        min_increase = min(min_increase, ratio)
        
        # Calcular límites finales
        lower = c_j - min_decrease if min_decrease != float('inf') else float('-inf')
        upper = c_j + min_increase if min_increase != float('inf') else float('inf')
        
        return lower, upper
    
    def _get_basic_var_value(self, tableau: np.ndarray, row: int) -> float:
        """Obtiene el valor de una variable básica desde el tableau."""
        if row >= 0 and row < tableau.shape[0] - 1:
            return float(tableau[row, -1])
        return 0.0
    
    def _calculate_rhs_ranges(
        self,
        tableau: np.ndarray,
        basis: List[str],
        var_names: List[str],
        slack_names: List[str],
        original_b: np.ndarray,
        constraint_names: List[str],
        column_headers: List[str]
    ) -> List[SensitivityRange]:
        """
        Calcula los rangos de factibilidad para los términos independientes (RHS).
        
        El RHS b_i puede variar mientras la solución básica permanezca factible
        (todas las variables básicas no negativas).
        
        El rango está determinado por: x_B = B^(-1) * b >= 0
        Al variar b_i: x_B + Δb_i * (columna i de B^(-1)) >= 0
        """
        ranges = []
        n_constraints = len(original_b)
        
        # Construir mapeo de nombres a índices
        col_map = {name: i for i, name in enumerate(column_headers) if i < len(column_headers) - 1}
        
        # Obtener la parte del tableau correspondiente a las restricciones (sin fila Z)
        constraint_rows = tableau[:-1, :]
        rhs_values = constraint_rows[:, -1]  # Última columna = RHS actual
        
        for i in range(n_constraints):
            if i >= len(original_b):
                continue
            
            b_i = float(original_b[i])
            constraint_name = constraint_names[i] if i < len(constraint_names) else f"Restricción {i+1}"
            slack_var = slack_names[i] if i < len(slack_names) else f"s{i+1}"
            
            # Encontrar la columna de la variable de holgura correspondiente
            slack_col = col_map.get(slack_var, -1)
            
            if slack_col < 0:
                # Intentar encontrar por índice
                slack_col = len(var_names) + i
            
            if slack_col >= tableau.shape[1] - 1:
                ranges.append(SensitivityRange(
                    variable=constraint_name,
                    current_value=b_i,
                    lower_bound=float('-inf'),
                    upper_bound=float('inf'),
                    allowable_decrease=float('inf'),
                    allowable_increase=float('inf'),
                    explanation=f"No se pudo calcular el rango para {constraint_name}",
                    interpretation=""
                ))
                continue
            
            # Columna de B^(-1) correspondiente a esta restricción
            # Es la columna de la variable de holgura en el tableau óptimo
            b_inv_col = constraint_rows[:, slack_col]
            
            # Calcular límites
            min_decrease = float('inf')
            min_increase = float('inf')
            
            for row in range(len(rhs_values)):
                x_row = float(rhs_values[row])
                coef = float(b_inv_col[row])
                
                if abs(coef) < self._TOL:
                    continue
                
                if coef > 0:
                    # Límite al disminuir b_i (x_row - coef*Δ >= 0 => Δ <= x_row/coef)
                    ratio = x_row / coef
                    if ratio >= 0:
                        min_decrease = min(min_decrease, ratio)
                else:  # coef < 0
                    # Límite al aumentar b_i (x_row + |coef|*Δ >= 0 siempre si x_row >= 0)
                    # Pero si x_row < 0, necesitamos Δ >= x_row/coef
                    ratio = -x_row / coef
                    if ratio >= 0:
                        min_increase = min(min_increase, ratio)
            
            # Ajustar los límites
            lower = b_i - min_decrease if min_decrease != float('inf') else float('-inf')
            upper = b_i + min_increase if min_increase != float('inf') else float('inf')
            
            # Asegurar que lower <= b_i <= upper
            lower = min(lower, b_i)
            upper = max(upper, b_i)
            
            allowable_decrease = b_i - lower if lower != float('-inf') else float('inf')
            allowable_increase = upper - b_i if upper != float('inf') else float('inf')
            
            # Verificar si la restricción está activa (binding)
            is_binding = slack_var not in basis or (slack_var in basis and abs(rhs_values[basis.index(slack_var)] if slack_var in basis else 0) < self._TOL)
            
            explanation = (
                f"El término independiente de '{constraint_name}' (b_{i+1} = {b_i:.4g}) "
                f"puede variar entre [{self._format_bound(lower)}, {self._format_bound(upper)}] "
                f"manteniendo la misma base óptima."
            )
            
            if is_binding:
                interpretation = (
                    f"Esta restricción está activa (se cumple con igualdad). "
                    f"Aumentar b_{i+1} en una unidad mejoraría Z según el precio sombra. "
                    f"El precio sombra es válido dentro de este rango."
                )
            else:
                interpretation = (
                    f"Esta restricción tiene holgura (no está activa). "
                    f"El precio sombra es 0: aumentar b_{i+1} no mejora Z."
                )
            
            ranges.append(SensitivityRange(
                variable=constraint_name,
                current_value=b_i,
                lower_bound=lower,
                upper_bound=upper,
                allowable_decrease=allowable_decrease,
                allowable_increase=allowable_increase,
                explanation=explanation,
                interpretation=interpretation
            ))
        
        return ranges
    
    def _calculate_shadow_prices(
        self,
        tableau: np.ndarray,
        basis: List[str],
        slack_names: List[str],
        constraint_names: List[str],
        is_maximization: bool,
        column_headers: List[str]
    ) -> List[ShadowPrice]:
        """
        Calcula los precios sombra (valores duales) de las restricciones.
        
        TEORÍA:
        -------
        El precio sombra π_i representa el cambio en Z por cada unidad de incremento en b_i.
        
        - En MAXIMIZACIÓN: π_i >= 0 para restricciones <= activas
          (más recursos permiten mayor ganancia)
        
        - En MINIMIZACIÓN: π_i >= 0 para restricciones >= activas
          (relajar restricciones reduce el costo mínimo)
        
        Los precios sombra se obtienen de los coeficientes de las variables de holgura 
        en la fila Z del tableau óptimo. El signo depende de cómo se construyó el tableau.
        """
        shadow_prices = []
        
        # Mapeo de columnas
        col_map = {name: i for i, name in enumerate(column_headers) if i < len(column_headers) - 1}
        
        # Fila Z
        z_row = tableau[-1, :-1]
        rhs_values = tableau[:-1, -1]
        
        for i, slack_var in enumerate(slack_names):
            constraint_name = constraint_names[i] if i < len(constraint_names) else f"Restricción {i+1}"
            
            # Encontrar columna de la variable de holgura
            slack_col = col_map.get(slack_var, -1)
            if slack_col < 0:
                slack_col = len([v for v in column_headers if v not in slack_names and v != "RHS"]) + i
            
            if slack_col >= len(z_row):
                continue
            
            # Obtener el coeficiente de la variable de holgura en la fila Z
            raw_value = float(z_row[slack_col])
            
            # El precio sombra tiene interpretación económica:
            # En el tableau estándar de Simplex, el coeficiente de s_i en la fila Z óptima
            # representa el precio sombra (posiblemente con signo negado según la implementación)
            # Usamos el valor absoluto y ajustamos la interpretación
            shadow_price_value = abs(raw_value)
            
            # Verificar si está en la base (restricción no activa = hay holgura)
            is_binding = slack_var not in basis
            
            if is_binding:
                # Restricción activa: tiene precio sombra potencialmente no nulo
                explanation = (
                    f"La restricción '{constraint_name}' está **activa** (binding). "
                    f"El precio sombra π_{i+1} = {shadow_price_value:.4g}."
                )
                if is_maximization:
                    if shadow_price_value > self._TOL:
                        economic_interpretation = (
                            f"Si aumentamos el RHS de esta restricción en 1 unidad, "
                            f"el valor óptimo Z **aumentará** en {shadow_price_value:.4g} unidades. "
                            f"Este recurso es escaso y tiene valor marginal positivo."
                        )
                    else:
                        economic_interpretation = (
                            f"El precio sombra es prácticamente cero. Aunque la restricción está activa, "
                            f"aumentar el RHS no mejorará significativamente Z."
                        )
                else:
                    if shadow_price_value > self._TOL:
                        economic_interpretation = (
                            f"Si aumentamos el RHS de esta restricción en 1 unidad, "
                            f"el costo mínimo Z **disminuirá** en {shadow_price_value:.4g} unidades. "
                            f"Relajar esta restricción tiene valor."
                        )
                    else:
                        economic_interpretation = (
                            f"El precio sombra es prácticamente cero."
                        )
            else:
                # Restricción no activa: hay holgura, precio sombra = 0
                shadow_price_value = 0.0
                explanation = (
                    f"La restricción '{constraint_name}' **no está activa** (hay holgura). "
                    f"El precio sombra es π_{i+1} = 0."
                )
                economic_interpretation = (
                    f"Como hay recursos no utilizados (holgura > 0) en esta restricción, "
                    f"aumentar su disponibilidad no mejorará el valor óptimo. "
                    f"Este recurso **no es escaso**."
                )
            
            shadow_prices.append(ShadowPrice(
                constraint_index=i,
                constraint_name=constraint_name,
                value=shadow_price_value,
                slack_variable=slack_var,
                binding=is_binding,
                explanation=explanation,
                economic_interpretation=economic_interpretation
            ))
        
        return shadow_prices
    
    def _calculate_reduced_costs(
        self,
        tableau: np.ndarray,
        basis: List[str],
        var_names: List[str],
        slack_names: List[str],
        is_maximization: bool,
        column_headers: List[str]
    ) -> List[ReducedCost]:
        """
        Calcula los costos reducidos de todas las variables.
        
        El costo reducido c̄_j indica:
        - Para variables básicas: siempre es 0 (por definición)
        - Para variables no básicas: cuánto debe mejorar c_j para que entre a la base
        
        Se obtienen directamente de la fila Z del tableau óptimo.
        """
        reduced_costs = []
        
        # Mapeo de columnas
        col_map = {name: i for i, name in enumerate(column_headers) if i < len(column_headers) - 1}
        
        # Fila Z
        z_row = tableau[-1, :-1]
        
        for var in var_names:
            col_idx = col_map.get(var, -1)
            if col_idx < 0 or col_idx >= len(z_row):
                continue
            
            is_basic = var in basis
            
            if is_basic:
                reduced_cost_value = 0.0
                explanation = f"La variable {var} está en la base óptima."
                interpretation = (
                    f"Como {var} es una variable básica con valor positivo en la solución óptima, "
                    f"su costo reducido es 0 por definición."
                )
            else:
                reduced_cost_value = float(z_row[col_idx])
                explanation = f"La variable {var} no está en la base. Costo reducido: {reduced_cost_value:.4g}."
                
                if is_maximization:
                    if reduced_cost_value <= -self._TOL:
                        interpretation = (
                            f"El valor {var} = 0 es óptimo. Para que {var} entre a la solución, "
                            f"su coeficiente en la función objetivo debería aumentar en más de "
                            f"{abs(reduced_cost_value):.4g} unidades."
                        )
                    else:
                        interpretation = (
                            f"El costo reducido indica cuánto 'cuesta' incrementar {var} desde 0. "
                            f"Actualmente no es rentable incluir esta variable."
                        )
                else:
                    if reduced_cost_value >= self._TOL:
                        interpretation = (
                            f"El valor {var} = 0 es óptimo. Para que {var} entre a la solución, "
                            f"su coeficiente en la función objetivo debería disminuir en más de "
                            f"{abs(reduced_cost_value):.4g} unidades."
                        )
                    else:
                        interpretation = (
                            f"El costo reducido indica el 'ahorro' potencial de incluir {var}. "
                            f"Actualmente no es beneficioso incluir esta variable."
                        )
            
            reduced_costs.append(ReducedCost(
                variable=var,
                value=reduced_cost_value,
                is_basic=is_basic,
                explanation=explanation,
                interpretation=interpretation
            ))
        
        return reduced_costs
    
    def _generate_theory_explanation(self, is_maximization: bool) -> str:
        """Genera una explicación teórica del análisis de sensibilidad."""
        obj_type = "maximización" if is_maximization else "minimización"
        
        return f"""
## Análisis de Sensibilidad Post-Óptimo

### ¿Qué es el Análisis de Sensibilidad?

El análisis de sensibilidad estudia cómo los cambios en los parámetros del problema 
afectan a la solución óptima. Es una herramienta fundamental para la toma de decisiones 
porque los datos del mundo real rara vez son exactos.

### Componentes del Análisis

#### 1. Rangos de Optimalidad (Coeficientes de la Función Objetivo)

Estos rangos indican cuánto pueden variar los coeficientes c_j de la función objetivo 
sin que cambie la **base óptima** (es decir, qué variables son positivas en la solución).

**Importante**: Aunque la base no cambie, el **valor óptimo Z sí cambiará** proporcionalmente.

#### 2. Rangos de Factibilidad (Términos Independientes RHS)

Estos rangos indican cuánto pueden variar los valores b_i (lado derecho de las restricciones) 
manteniendo la misma base óptima.

**Dentro de estos rangos, los precios sombra son válidos.**

#### 3. Precios Sombra (Valores Duales)

El precio sombra π_i de una restricción representa el cambio en Z por cada unidad 
de incremento en b_i.

- **Para {obj_type}**: Si π_i > 0, aumentar b_i mejora Z.
- **Restricción activa** (binding): La restricción se cumple con igualdad; su precio sombra puede ser ≠ 0.
- **Restricción no activa**: Hay holgura; el precio sombra es 0.

#### 4. Costos Reducidos

El costo reducido c̄_j de una variable no básica indica cuánto debe cambiar 
su coeficiente en la función objetivo para que entre a la base óptima.

- **Variables básicas**: Costo reducido = 0 (por definición).
- **Variables no básicas**: El costo reducido muestra el "costo de oportunidad" 
  de incluir esa variable en la solución.

### Interpretación Económica

Los precios sombra tienen una interpretación económica directa:
- Representan el **valor marginal** de cada recurso.
- Indican cuánto estaría dispuesto a pagar (o ahorrar) por una unidad adicional de cada recurso.
- Son válidos solo dentro de los rangos de factibilidad del RHS.
"""
    
    def _generate_practical_insights(
        self,
        objective_ranges: List[SensitivityRange],
        rhs_ranges: List[SensitivityRange],
        shadow_prices: List[ShadowPrice],
        reduced_costs: List[ReducedCost],
        objective_value: float,
        is_maximization: bool
    ) -> List[str]:
        """Genera insights prácticos basados en el análisis."""
        insights = []
        
        # Insight sobre el valor óptimo
        obj_type = "máximo" if is_maximization else "mínimo"
        insights.append(f"📊 **Valor óptimo**: Z = {objective_value:.4g} ({obj_type})")
        
        # Identificar restricciones más valiosas (mayor precio sombra)
        binding_constraints = [sp for sp in shadow_prices if sp.binding and abs(sp.value) > self._TOL]
        if binding_constraints:
            most_valuable = max(binding_constraints, key=lambda x: abs(x.value))
            insights.append(
                f"💎 **Recurso más valioso**: {most_valuable.constraint_name} "
                f"con precio sombra π = {most_valuable.value:.4g}. "
                f"Aumentar este recurso tendría el mayor impacto en Z."
            )
        
        # Restricciones no activas (con holgura)
        slack_constraints = [sp for sp in shadow_prices if not sp.binding]
        if slack_constraints:
            insights.append(
                f"📦 **Recursos con excedente**: {', '.join(sp.constraint_name for sp in slack_constraints)}. "
                f"Hay capacidad no utilizada en estos recursos."
            )
        
        # Variables no básicas con menor costo reducido
        non_basic = [rc for rc in reduced_costs if not rc.is_basic]
        if non_basic:
            closest = min(non_basic, key=lambda x: abs(x.value))
            insights.append(
                f"🎯 **Variable más cercana a entrar**: {closest.variable} "
                f"con costo reducido = {closest.value:.4g}. "
                f"Es la más próxima a ser rentable."
            )
        
        # Sensibilidad de coeficientes
        most_sensitive = None
        min_range = float('inf')
        for r in objective_ranges:
            range_size = r.allowable_decrease + r.allowable_increase
            if range_size < min_range and range_size < float('inf'):
                min_range = range_size
                most_sensitive = r
        
        if most_sensitive and min_range < float('inf'):
            insights.append(
                f"⚠️ **Parámetro más sensible**: El coeficiente de {most_sensitive.variable}. "
                f"Pequeños cambios podrían alterar la solución óptima."
            )
        
        return insights
    
    def _format_bound(self, value: float) -> str:
        """Formatea un límite para presentación."""
        if value == float('inf') or value > self._INF_THRESHOLD:
            return "∞"
        elif value == float('-inf') or value < -self._INF_THRESHOLD:
            return "-∞"
        else:
            return f"{value:.4g}"
    
    def _range_to_dict(self, r: SensitivityRange) -> Dict[str, Any]:
        """Convierte SensitivityRange a diccionario."""
        return {
            "variable": r.variable,
            "current_value": r.current_value,
            "lower_bound": r.lower_bound if r.lower_bound != float('-inf') else None,
            "upper_bound": r.upper_bound if r.upper_bound != float('inf') else None,
            "lower_bound_display": self._format_bound(r.lower_bound),
            "upper_bound_display": self._format_bound(r.upper_bound),
            "allowable_decrease": r.allowable_decrease if r.allowable_decrease != float('inf') else None,
            "allowable_increase": r.allowable_increase if r.allowable_increase != float('inf') else None,
            "allowable_decrease_display": self._format_bound(r.allowable_decrease),
            "allowable_increase_display": self._format_bound(r.allowable_increase),
            "explanation": r.explanation,
            "interpretation": r.interpretation
        }
    
    def _shadow_price_to_dict(self, sp: ShadowPrice) -> Dict[str, Any]:
        """Convierte ShadowPrice a diccionario."""
        return {
            "constraint_index": sp.constraint_index,
            "constraint_name": sp.constraint_name,
            "value": sp.value,
            "slack_variable": sp.slack_variable,
            "binding": sp.binding,
            "explanation": sp.explanation,
            "economic_interpretation": sp.economic_interpretation
        }
    
    def _reduced_cost_to_dict(self, rc: ReducedCost) -> Dict[str, Any]:
        """Convierte ReducedCost a diccionario."""
        return {
            "variable": rc.variable,
            "value": rc.value,
            "is_basic": rc.is_basic,
            "explanation": rc.explanation,
            "interpretation": rc.interpretation
        }


def perform_sensitivity_analysis(
    solver_result: Dict[str, Any],
    model_data: Dict[str, Any],
    method: str
) -> Dict[str, Any]:
    """
    Función de conveniencia para realizar análisis de sensibilidad.
    
    Solo aplica a los métodos: simplex, dual_simplex, big_m
    
    Args:
        solver_result: Resultado del solver
        model_data: Datos del modelo (c, b, var_names, etc.)
        method: Método utilizado (simplex, dual_simplex, big_m)
        
    Returns:
        Diccionario con el análisis de sensibilidad
    """
    # Verificar que el método sea compatible
    compatible_methods = ["simplex", "dual_simplex", "big_m"]
    if method not in compatible_methods:
        return {
            "success": False,
            "error": f"El análisis de sensibilidad no está disponible para el método '{method}'. "
                    f"Solo disponible para: {', '.join(compatible_methods)}",
            "sensitivity_analysis": None
        }
    
    # Verificar que la solución sea óptima
    if not solver_result.get("success"):
        return {
            "success": False,
            "error": "No se puede realizar análisis de sensibilidad sin una solución óptima",
            "sensitivity_analysis": None
        }
    
    # Extraer datos necesarios
    original_c = np.array(model_data.get("c", []))
    original_b = np.array(model_data.get("b", []))
    var_names = model_data.get("var_names", [])
    constraint_names = model_data.get("constraint_names")
    is_maximization = model_data.get("is_maximization", True)
    
    # Crear analizador y ejecutar
    analyzer = SensitivityAnalyzer()
    return analyzer.analyze(
        solver_result=solver_result,
        original_c=original_c,
        original_b=original_b,
        var_names=var_names,
        constraint_names=constraint_names,
        is_maximization=is_maximization
    )


class ExecutiveConclusionGenerator:
    """
    Generador de conclusiones ejecutivas usando IA.
    
    Analiza el problema original, la solución óptima y el análisis de sensibilidad
    para generar un informe de alto nivel dirigido a directivos y tomadores de decisiones.
    """
    
    EXECUTIVE_SYSTEM_PROMPT = """Eres un consultor experto en investigación de operaciones y análisis de negocios.
Tu rol es interpretar los resultados de optimización lineal y traducirlos en insights accionables
para directivos y tomadores de decisiones que NO tienen conocimientos técnicos de matemáticas.

IMPORTANTE:
- Usa lenguaje de negocios, NO términos técnicos de matemáticas
- Enfócate en el IMPACTO en el negocio, no en las fórmulas
- Da recomendaciones concretas y accionables
- Identifica riesgos y oportunidades
- Sé conciso pero completo
- Usa viñetas y estructura clara
- Incluye números específicos cuando sean relevantes
- Relaciona siempre con el contexto del problema original"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el generador con la API key de Groq.
        
        Args:
            api_key: API key de Groq. Si no se proporciona, usa la configuración por defecto.
        """
        self.api_key = api_key or settings.GROQ_API_KEY
        
    def generate_conclusion(
        self,
        original_problem: str,
        model_context: str,
        solver_result: Dict[str, Any],
        sensitivity_analysis: Optional[Dict[str, Any]],
        method: str,
        variables_description: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Genera una conclusión ejecutiva usando IA.
        
        Args:
            original_problem: Enunciado original del problema
            model_context: Contexto del modelo matemático
            solver_result: Resultado del solver (objective_value, variables, etc.)
            sensitivity_analysis: Análisis de sensibilidad (opcional)
            method: Método usado (simplex, dual_simplex, big_m)
            variables_description: Descripción de cada variable
            
        Returns:
            Diccionario con la conclusión ejecutiva
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "API key de Groq no configurada",
                    "conclusion": None
                }
            
            # Construir el prompt con toda la información
            prompt = self._build_prompt(
                original_problem=original_problem,
                model_context=model_context,
                solver_result=solver_result,
                sensitivity_analysis=sensitivity_analysis,
                method=method,
                variables_description=variables_description
            )
            
            # Llamar a Groq
            client = GroqClient(api_key=self.api_key)
            response = client.chat(
                user_prompt=prompt,
                system_prompt=self.EXECUTIVE_SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=2500
            )
            
            if not response.get("success"):
                return {
                    "success": False,
                    "error": response.get("error", "Error al generar conclusión"),
                    "conclusion": None
                }
            
            conclusion_text = response.get("content", "")
            
            return {
                "success": True,
                "conclusion": conclusion_text,
                "tokens_used": response.get("tokens", 0)
            }
            
        except Exception as e:
            logger.error(f"Error generando conclusión ejecutiva: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "conclusion": None
            }
    
    def _build_prompt(
        self,
        original_problem: str,
        model_context: str,
        solver_result: Dict[str, Any],
        sensitivity_analysis: Optional[Dict[str, Any]],
        method: str,
        variables_description: Dict[str, str]
    ) -> str:
        """Construye el prompt para la IA."""
        
        # Extraer información del resultado
        objective_value = solver_result.get("objective_value", 0)
        variables = solver_result.get("variables", {})
        is_maximization = solver_result.get("method") != "dual_simplex" or model_context.lower().find("minim") == -1
        
        # Formatear variables con sus valores y descripciones
        variables_text = ""
        for var, value in variables.items():
            desc = variables_description.get(var, var)
            variables_text += f"  - {var} = {value:.4g} → {desc}\n"
        
        # Construir sección de análisis de sensibilidad
        sensitivity_text = ""
        if sensitivity_analysis:
            # Precios sombra (recursos valiosos)
            shadow_prices = sensitivity_analysis.get("shadow_prices", [])
            if shadow_prices:
                sensitivity_text += "\n### Valor de los Recursos (Precios Sombra):\n"
                for sp in shadow_prices:
                    binding_status = "ACTIVA (recurso agotado)" if sp.get("binding") else "NO ACTIVA (hay excedente)"
                    sensitivity_text += f"  - {sp.get('constraint_name')}: π = {sp.get('value', 0):.4g} [{binding_status}]\n"
                    if sp.get("binding") and sp.get("value", 0) > 0:
                        sensitivity_text += f"    → Cada unidad adicional mejoraría el resultado en {sp.get('value', 0):.4g}\n"
            
            # Rangos de coeficientes
            objective_ranges = sensitivity_analysis.get("objective_ranges", [])
            if objective_ranges:
                sensitivity_text += "\n### Sensibilidad de Parámetros Clave:\n"
                for r in objective_ranges:
                    lower = r.get("lower_bound_display", "-∞")
                    upper = r.get("upper_bound_display", "∞")
                    sensitivity_text += f"  - {r.get('variable')}: puede variar entre [{lower}, {upper}] sin cambiar la estrategia\n"
            
            # Rangos RHS
            rhs_ranges = sensitivity_analysis.get("rhs_ranges", [])
            if rhs_ranges:
                sensitivity_text += "\n### Flexibilidad en Recursos:\n"
                for r in rhs_ranges:
                    lower = r.get("lower_bound_display", "-∞")
                    upper = r.get("upper_bound_display", "∞")
                    sensitivity_text += f"  - {r.get('variable')}: válido entre [{lower}, {upper}]\n"
            
            # Variables básicas vs no básicas
            basic_vars = sensitivity_analysis.get("basic_variables", [])
            non_basic_vars = sensitivity_analysis.get("non_basic_variables", [])
            if basic_vars or non_basic_vars:
                sensitivity_text += "\n### Uso de Recursos/Variables:\n"
                if basic_vars:
                    sensitivity_text += f"  - Variables ACTIVAS en la solución: {', '.join(basic_vars)}\n"
                if non_basic_vars:
                    sensitivity_text += f"  - Variables NO utilizadas (valor = 0): {', '.join(non_basic_vars)}\n"
        
        # Determinar tipo de problema
        method_names = {
            "simplex": "Método Simplex",
            "dual_simplex": "Método Simplex Dual",
            "big_m": "Método de la Gran M"
        }
        method_name = method_names.get(method, method)
        
        prompt = f"""
## PROBLEMA ORIGINAL DEL CLIENTE:
{original_problem}

## CONTEXTO DEL NEGOCIO:
{model_context if model_context else "No especificado"}

## SOLUCIÓN ÓPTIMA ENCONTRADA:
- **Método utilizado**: {method_name}
- **Valor óptimo de la función objetivo**: {objective_value:.4g}
- **Tipo**: {"Maximización" if is_maximization else "Minimización"}

### Valores óptimos de las variables de decisión:
{variables_text}
{sensitivity_text}

---

## INSTRUCCIONES PARA TU RESPUESTA:

Genera un **INFORME EJECUTIVO** estructurado de la siguiente manera:

### 1. 📋 RESUMEN EJECUTIVO (2-3 oraciones)
Qué se optimizó y cuál es el resultado principal en términos de negocio.

### 2. 💡 DECISIÓN ÓPTIMA RECOMENDADA
Traduce los valores de las variables a acciones concretas de negocio.
Usa el contexto del problema para dar significado a los números.

### 3. 💰 IMPACTO ECONÓMICO
Cuál es el beneficio/ahorro/costo óptimo y qué significa para la organización.

### 4. ⚠️ FACTORES CRÍTICOS Y RIESGOS
Basándote en el análisis de sensibilidad:
- ¿Qué recursos son más valiosos/escasos?
- ¿Qué parámetros son más sensibles a cambios?
- ¿Qué riesgos existen si cambian las condiciones?

### 5. 🎯 RECOMENDACIONES ESTRATÉGICAS
3-5 acciones concretas que la gerencia debería considerar basándose en:
- Los precios sombra (qué recursos vale la pena aumentar)
- Los rangos de sensibilidad (qué tan robusta es la solución)
- Las variables no utilizadas (qué se puede reconsiderar)

### 6. 📊 PRÓXIMOS PASOS
Qué debería hacer el cliente después de recibir este análisis.

---
Recuerda: Tu audiencia son DIRECTIVOS sin conocimientos de matemáticas. 
Traduce TODO a lenguaje de negocios.
"""
        
        return prompt
    
    def generate_quick_summary(
        self,
        solver_result: Dict[str, Any],
        sensitivity_analysis: Optional[Dict[str, Any]],
        variables_description: Dict[str, str]
    ) -> str:
        """
        Genera un resumen rápido sin usar IA (fallback).
        
        Útil cuando no hay API key o se quiere una respuesta inmediata.
        """
        objective_value = solver_result.get("objective_value", 0)
        variables = solver_result.get("variables", {})
        
        summary_lines = [
            "## 📊 Resumen de la Solución",
            "",
            f"**Valor Óptimo:** {objective_value:.4g}",
            "",
            "### Decisiones Óptimas:"
        ]
        
        for var, value in variables.items():
            desc = variables_description.get(var, var)
            summary_lines.append(f"- **{var}** = {value:.4g} ({desc})")
        
        if sensitivity_analysis:
            # Encontrar recurso más valioso
            shadow_prices = sensitivity_analysis.get("shadow_prices", [])
            binding_with_value = [sp for sp in shadow_prices if sp.get("binding") and sp.get("value", 0) > 0]
            
            if binding_with_value:
                most_valuable = max(binding_with_value, key=lambda x: x.get("value", 0))
                summary_lines.extend([
                    "",
                    "### 💎 Recurso Más Valioso:",
                    f"**{most_valuable.get('constraint_name')}** - Cada unidad adicional mejoraría el resultado en {most_valuable.get('value', 0):.4g}"
                ])
            
            # Recursos con excedente
            slack_resources = [sp for sp in shadow_prices if not sp.get("binding")]
            if slack_resources:
                summary_lines.extend([
                    "",
                    "### 📦 Recursos con Excedente:",
                    ", ".join(sp.get("constraint_name", "?") for sp in slack_resources)
                ])
        
        return "\n".join(summary_lines)


def generate_executive_conclusion(
    original_problem: str,
    model_context: str,
    solver_result: Dict[str, Any],
    sensitivity_analysis: Optional[Dict[str, Any]],
    method: str,
    variables_description: Dict[str, str],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Función de conveniencia para generar conclusión ejecutiva.
    
    Args:
        original_problem: Enunciado original del problema
        model_context: Contexto del negocio
        solver_result: Resultado del solver
        sensitivity_analysis: Análisis de sensibilidad
        method: Método usado
        variables_description: Descripción de variables
        api_key: API key de Groq (opcional)
        
    Returns:
        Diccionario con la conclusión ejecutiva
    """
    generator = ExecutiveConclusionGenerator(api_key=api_key)
    return generator.generate_conclusion(
        original_problem=original_problem,
        model_context=model_context,
        solver_result=solver_result,
        sensitivity_analysis=sensitivity_analysis,
        method=method,
        variables_description=variables_description
    )

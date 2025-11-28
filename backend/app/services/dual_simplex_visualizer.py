"""
DualSimplexVisualizer: Generador de visualizaciones HTML/LaTeX para el método Simplex Dual.

Genera tablas Simplex con:
- Colores para identificar filas y columnas pivote
- Highlighting del elemento pivote
- Explicaciones paso a paso
- Razones duales mostradas visualmente
- Variables de holgura resaltadas
"""

from typing import Dict, List, Any, Optional
import numpy as np


class DualSimplexVisualizer:
    """Generador de visualizaciones para el método Simplex Dual."""
    
    # Colores para la visualización
    COLORS = {
        "pivot_cell": "#ff4444",      # Rojo para elemento pivote
        "pivot_row": "#ffcccc",       # Rosa claro para fila pivote
        "pivot_col": "#ccccff",       # Azul claro para columna pivote
        "header": "#4CAF50",          # Verde para encabezados
        "basis": "#FFC107",           # Amarillo para variables básicas
        "optimal": "#4CAF50",         # Verde para solución óptima
        "infeasible": "#f44336",      # Rojo para infactible
        "negative_rhs": "#ff9800",    # Naranja para RHS negativos
        "slack_var": "#e1bee7",       # Púrpura claro para variables de holgura
    }
    
    def generate_html_visualization(self, steps: List[Dict[str, Any]]) -> str:
        """
        Genera visualización HTML completa con todas las iteraciones.
        
        Args:
            steps: Lista de pasos del Simplex Dual
            
        Returns:
            String HTML con la visualización completa
        """
        html_parts = [self._generate_html_header()]
        
        for step in steps:
            html_parts.append(self._generate_step_html(step))
        
        html_parts.append(self._generate_html_footer())
        
        return "\n".join(html_parts)
    
    def _generate_html_header(self) -> str:
        """Genera el encabezado HTML con estilos CSS."""
        return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Método Simplex Dual - Visualización</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 20px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .iteration-container {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .iteration-header {{
            background: {self.COLORS["header"]};
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 1.2em;
            font-weight: bold;
        }}
        
        .tableau-table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            font-size: 14px;
        }}
        
        .tableau-table th {{
            background-color: {self.COLORS["header"]};
            color: white;
            padding: 12px;
            text-align: center;
            font-weight: bold;
        }}
        
        .tableau-table td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: center;
        }}
        
        .tableau-table tr:hover {{
            background-color: #f5f5f5;
        }}
        
        .basis-column {{
            background-color: {self.COLORS["basis"]};
            font-weight: bold;
        }}
        
        .pivot-cell {{
            background-color: {self.COLORS["pivot_cell"]} !important;
            color: white;
            font-weight: bold;
            font-size: 1.1em;
            border: 3px solid #cc0000 !important;
        }}
        
        .pivot-row {{
            background-color: {self.COLORS["pivot_row"]};
        }}
        
        .pivot-column {{
            background-color: {self.COLORS["pivot_col"]};
        }}
        
        .negative-rhs {{
            background-color: {self.COLORS["negative_rhs"]};
            color: white;
            font-weight: bold;
        }}
        
        .slack-var {{
            background-color: {self.COLORS["slack_var"]};
        }}
        
        .explanation-box {{
            background-color: #e3f2fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        
        .dual-ratios-box {{
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        
        .ratios-table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 10px;
        }}
        
        .ratios-table th,
        .ratios-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }}
        
        .ratios-table th {{
            background-color: #ff9800;
            color: white;
        }}
        
        .minimum-ratio {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        
        .status-optimal {{
            background-color: {self.COLORS["optimal"]};
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            text-align: center;
            font-weight: bold;
        }}
        
        .status-infeasible {{
            background-color: {self.COLORS["infeasible"]};
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            text-align: center;
            font-weight: bold;
        }}
        
        .variable-addition {{
            background-color: #f1f8e9;
            border: 2px dashed #8bc34a;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        
        .variable-addition h4 {{
            color: #558b2f;
            margin-top: 0;
        }}
        
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin: 20px 0;
            padding: 15px;
            background-color: #fafafa;
            border-radius: 5px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-color {{
            width: 30px;
            height: 20px;
            border: 1px solid #999;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <h1 style="text-align: center; color: #333;">Método Simplex Dual - Solución Paso a Paso</h1>
    
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.COLORS["pivot_cell"]};"></div>
            <span>Elemento Pivote</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.COLORS["pivot_row"]};"></div>
            <span>Fila Pivote</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.COLORS["pivot_col"]};"></div>
            <span>Columna Pivote</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.COLORS["negative_rhs"]};"></div>
            <span>RHS Negativo</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.COLORS["slack_var"]};"></div>
            <span>Variable de Holgura</span>
        </div>
    </div>
"""
    
    def _generate_html_footer(self) -> str:
        """Genera el pie de página HTML."""
        return """
</body>
</html>
"""
    
    def _generate_step_html(self, step: Dict[str, Any]) -> str:
        """
        Genera el HTML para un paso individual.
        """
        iteration = step.get("iteration", 0)
        description = step.get("description", "")
        step_type = step.get("type", "iteration")
        
        html = f'<div class="iteration-container">\n'
        html += f'<div class="iteration-header">Iteración {iteration}: {description}</div>\n'
        
        # Mostrar variables de holgura agregadas (solo en paso inicial)
        if iteration == 0:
            html += self._generate_slack_variables_info(step)
        
        # Explicación del paso
        if step.get("reasoning"):
            html += self._generate_explanation_box(step["reasoning"])
        
        # Tabla de razones duales (si existen)
        if step.get("dual_ratios"):
            html += self._generate_dual_ratios_table(step["dual_ratios"])
        
        # Tableau
        html += self._generate_tableau_html(step)
        
        # Estado de factibilidad
        html += self._generate_feasibility_status(step)
        
        html += '</div>\n'
        
        return html
    
    def _generate_slack_variables_info(self, step: Dict[str, Any]) -> str:
        """
        Genera información sobre las variables de holgura agregadas.
        """
        slack_names = step.get("slack_names", [])
        
        if not slack_names:
            return ""
        
        html = '<div class="variable-addition">\n'
        html += '<h4>📊 Variables de Holgura Agregadas</h4>\n'
        html += '<p>Para convertir las restricciones en ecuaciones, se agregan las siguientes variables de holgura:</p>\n'
        html += '<ul>\n'
        
        for slack in slack_names:
            html += f'<li><strong>{slack}</strong> - Variable de holgura</li>\n'
        
        html += '</ul>\n'
        
        reasoning = step.get("reasoning", {})
        if reasoning.get("explanation"):
            html += f'<p><em>{reasoning["explanation"]}</em></p>\n'
        
        html += '</div>\n'
        
        return html
    
    def _generate_explanation_box(self, reasoning: Dict[str, Any]) -> str:
        """
        Genera una caja de explicación para el paso.
        """
        html = '<div class="explanation-box">\n'
        html += '<h4>📝 Explicación del Paso</h4>\n'
        
        explanation = reasoning.get("explanation", "")
        if explanation:
            html += f'<p><strong>{explanation}</strong></p>\n'
        
        # Detalles adicionales
        if reasoning.get("entering_variable"):
            html += f'<p>✅ <strong>Variable Entrante:</strong> {reasoning["entering_variable"]}</p>\n'
        
        if reasoning.get("leaving_variable"):
            html += f'<p>❌ <strong>Variable Saliente:</strong> {reasoning["leaving_variable"]}</p>\n'
        
        if reasoning.get("pivot_element") is not None:
            html += f'<p>🎯 <strong>Elemento Pivote:</strong> {reasoning["pivot_element"]:.4f}</p>\n'
        
        if reasoning.get("leaving_row_rhs_before") is not None:
            rhs = reasoning["leaving_row_rhs_before"]
            html += f'<p>📍 <strong>RHS de fila pivote (antes):</strong> {rhs:.4f} {"(NEGATIVO)" if rhs < 0 else ""}</p>\n'
        
        html += '</div>\n'
        
        return html
    
    def _generate_dual_ratios_table(self, dual_ratios: List[Dict[str, Any]]) -> str:
        """
        Genera una tabla mostrando las razones duales calculadas.
        """
        html = '<div class="dual-ratios-box">\n'
        html += '<h4>📊 Cálculo de Razones Duales</h4>\n'
        html += '<p>Razón = |Coeficiente Z / Coeficiente Fila Pivote| (solo para coeficientes negativos en fila pivote)</p>\n'
        html += '<table class="ratios-table">\n'
        html += '<thead><tr>\n'
        html += '<th>Columna</th>\n'
        html += '<th>Coef. Z</th>\n'
        html += '<th>Coef. Fila Pivote</th>\n'
        html += '<th>Razón</th>\n'
        html += '<th>¿Mínima?</th>\n'
        html += '</tr></thead>\n'
        html += '<tbody>\n'
        
        for ratio_info in dual_ratios:
            col = ratio_info.get("column", 0)
            obj_coeff = ratio_info.get("obj_coeff", 0)
            pivot_coeff = ratio_info.get("pivot_row_coeff", 0)
            ratio = ratio_info.get("ratio", 0)
            is_min = ratio_info.get("is_minimum", False)
            
            row_class = 'class="minimum-ratio"' if is_min else ''
            
            html += f'<tr {row_class}>\n'
            html += f'<td>{col}</td>\n'
            html += f'<td>{obj_coeff:.4f}</td>\n'
            html += f'<td>{pivot_coeff:.4f}</td>\n'
            html += f'<td>{ratio:.4f}</td>\n'
            html += f'<td>{"✓ SÍ" if is_min else "No"}</td>\n'
            html += '</tr>\n'
        
        html += '</tbody></table>\n'
        html += '</div>\n'
        
        return html
    
    def _generate_tableau_html(self, step: Dict[str, Any]) -> str:
        """
        Genera la tabla HTML del tableau con colores para pivotes.
        """
        tableau = step.get("tableau_after") or step.get("tableau")
        if not tableau:
            return ""
        
        column_headers = step.get("column_headers", [])
        row_labels = step.get("row_labels", [])
        pivot_row = step.get("pivot_row")
        pivot_col = step.get("pivot_column")
        slack_names = step.get("slack_names", [])
        
        html = '<table class="tableau-table">\n'
        
        # Encabezado
        html += '<thead><tr>\n'
        html += '<th>Base</th>\n'
        for j, header in enumerate(column_headers):
            col_class = "pivot-column" if j == pivot_col else ""
            slack_class = "slack-var" if header in slack_names else ""
            combined_class = f'{col_class} {slack_class}'.strip()
            class_attr = f'class="{combined_class}"' if combined_class else ''
            html += f'<th {class_attr}>{header}</th>\n'
        html += '</tr></thead>\n'
        
        # Cuerpo
        html += '<tbody>\n'
        for i, row in enumerate(tableau):
            row_class = "pivot-row" if i == pivot_row else ""
            class_attr = f'class="{row_class}"' if row_class else ''
            
            html += f'<tr {class_attr}>\n'
            
            # Etiqueta de fila (variable básica)
            basis_label = row_labels[i] if i < len(row_labels) else ""
            html += f'<td class="basis-column">{basis_label}</td>\n'
            
            # Valores de la fila
            for j, value in enumerate(row):
                # Determinar clases CSS
                classes = []
                
                # Elemento pivote
                if i == pivot_row and j == pivot_col:
                    classes.append("pivot-cell")
                # Columna pivote
                elif j == pivot_col:
                    classes.append("pivot-column")
                # Fila pivote
                elif i == pivot_row:
                    classes.append("pivot-row")
                
                # RHS negativo (última columna y valor negativo)
                if j == len(row) - 1 and value < -0.0001 and i < len(tableau) - 1:
                    classes.append("negative-rhs")
                
                # Variable de holgura
                if j < len(column_headers) and column_headers[j] in slack_names:
                    classes.append("slack-var")
                
                class_attr = f'class="{" ".join(classes)}"' if classes else ''
                
                # Formatear valor
                value_str = f"{value:.4f}" if abs(value) > 0.0001 else "0"
                
                html += f'<td {class_attr}>{value_str}</td>\n'
            
            html += '</tr>\n'
        
        html += '</tbody></table>\n'
        
        return html
    
    def _generate_feasibility_status(self, step: Dict[str, Any]) -> str:
        """
        Genera un indicador visual del estado de factibilidad.
        """
        is_feasible = step.get("is_feasible", False)
        status = step.get("status", "in_progress")
        
        if status == "optimal":
            return '<div class="status-optimal">✅ SOLUCIÓN ÓPTIMA ALCANZADA - Todos los RHS son no-negativos</div>\n'
        elif status == "infeasible":
            return '<div class="status-infeasible">❌ PROBLEMA INFACTIBLE - No existe solución que satisfaga todas las restricciones</div>\n'
        elif is_feasible:
            return '<div class="status-optimal">✅ Solución Factible (todos RHS ≥ 0)</div>\n'
        else:
            reasoning = step.get("reasoning", {})
            neg_count = reasoning.get("negative_rhs_count", 0)
            return f'<div class="explanation-box">⚠️ Solución Primal-Infactible: {neg_count} RHS negativos restantes</div>\n'
    
    def generate_latex_table(self, step: Dict[str, Any]) -> str:
        """
        Genera una tabla LaTeX para el tableau en un paso específico.
        """
        tableau = step.get("tableau_after") or step.get("tableau")
        if not tableau:
            return ""
        
        column_headers = step.get("column_headers", [])
        row_labels = step.get("row_labels", [])
        
        n_cols = len(column_headers)
        
        # Inicio de tabla
        latex = "\\begin{array}{c|" + "c" * n_cols + "}\n"
        
        # Encabezado
        latex += "\\text{Base} & " + " & ".join([f"\\text{{{h}}}" for h in column_headers]) + " \\\\\n"
        latex += "\\hline\n"
        
        # Filas
        for i, row in enumerate(tableau):
            basis_label = row_labels[i] if i < len(row_labels) else ""
            row_values = [f"{v:.4f}" if abs(v) > 0.0001 else "0" for v in row]
            latex += f"\\text{{{basis_label}}} & " + " & ".join(row_values) + " \\\\\n"
        
        latex += "\\end{array}\n"
        
        return latex

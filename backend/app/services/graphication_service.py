"""Servicio de graficación para problemas de PL con 2 variables."""

from typing import Dict, List, Tuple, Any
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import io, base64
from app.core.logger import logger

_TOL = 1e-10
_PRECISION = 4

class GraphicationService:
    """Genera gráficas del método gráfico para problemas con 2 variables."""

    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        self.figsize = figsize

    def generate_graphical_solution(self, model: 'MathematicalModel', 
                                    graphical_result: Dict[str, Any]) -> Dict[str, Any]:
        """Genera gráfica, tabla y bloque de solución."""
        try:
            if not graphical_result.get("success"):
                return {"success": False, "error": "Resultado inválido"}
            
            var_names = list(model.variables.keys())
            if len(var_names) != 2:
                return {"success": False, "error": "Se requieren 2 variables"}
            
            fig, ax = plt.subplots(figsize=self.figsize)
            x_name, y_name = var_names
            feasible_points = graphical_result.get("feasible_points", [])
            
            # Configurar límites y dibujar elementos
            x_lim, y_lim = self._compute_limits(feasible_points)
            x_range = np.linspace(-1, x_lim[1] * 1.1, 1000)
            
            self._plot_constraints(ax, graphical_result["constraints_info"], x_range, x_lim, y_lim)
            self._plot_feasible_region(ax, feasible_points)
            self._plot_vertices(ax, feasible_points)
            self._plot_level_curves(ax, x_range, graphical_result, x_name, y_name)
            self._configure_axes(ax, x_lim, y_lim, x_name, y_name, 
                               model.objective == "max")
            
            img_base64 = self._figure_to_base64(fig)
            plt.close(fig)
            
            return {
                "success": True,
                "image": img_base64,
                "vertices_table": self._generate_vertices_table(feasible_points),
                "solution_block": self._generate_solution_block(graphical_result, model),
                "explanation": graphical_result.get("explanation", "")
            }
        except Exception as e:
            logger.error(f"Error en graficación: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _compute_limits(self, feasible_points: List[Dict]) -> Tuple[Tuple, Tuple]:
        """Calcula límites de ejes basado en puntos factibles."""
        coords = [p["point"] for p in feasible_points] + [(0, 0), (10, 10)]
        xs, ys = zip(*coords)
        x_max, y_max = max(xs) * 1.2, max(ys) * 1.2
        return (0, max(x_max, 5)), (0, max(y_max, 5))

    def _plot_constraints(self, ax, constraints_info: List[Dict], x_range: np.ndarray, 
                         x_lim: Tuple, y_lim: Tuple) -> None:
        """Dibuja líneas de restricciones."""
        ax.axhline(y=0, color='black', linewidth=1, linestyle='-', alpha=0.3)
        ax.axvline(x=0, color='black', linewidth=1, linestyle='-', alpha=0.3)
        
        for c in constraints_info:
            a, b, rhs, label = c["a"], c["b"], c["rhs"], c["constraint"]
            if abs(b) > _TOL:
                ax.plot(x_range, (rhs - a*x_range)/b, 'b-', linewidth=2, alpha=0.7, label=label)
            elif abs(a) > _TOL:
                ax.axvline(x=rhs/a, color='b', linewidth=2, alpha=0.7, label=label)

    def _plot_feasible_region(self, ax, feasible_points: List[Dict]) -> None:
        """Sombrea la región factible."""
        if len(feasible_points) > 2:
            vertices = [p["point"] for p in feasible_points]
            sorted_v = self._sort_vertices(vertices)
            ax.add_patch(Polygon(sorted_v, alpha=0.3, facecolor='green', 
                               edgecolor='green', linewidth=2))

    def _plot_vertices(self, ax, feasible_points: List[Dict]) -> None:
        """Marca vértices y punto óptimo."""
        for pt in feasible_points:
            point, obj_val = pt["point"], pt["objective"]
            if pt.get("is_optimal"):
                ax.plot(point[0], point[1], 'r*', markersize=25, 
                       markeredgecolor='darkred', markeredgewidth=2, zorder=5,
                       label=f'Óptimo: ({point[0]:.2f}, {point[1]:.2f})')
            else:
                ax.plot(point[0], point[1], 'ko', markersize=8, zorder=4)
                ax.annotate(f'({point[0]:.2f}, {point[1]:.2f})\nz={obj_val:.2f}',
                          xy=point, xytext=(5, 5), textcoords='offset points',
                          fontsize=9, bbox=dict(boxstyle='round,pad=0.3', 
                                              facecolor='yellow', alpha=0.5), zorder=4)

    def _plot_level_curves(self, ax, x_range: np.ndarray, graphical_result: Dict, 
                          x_name: str, y_name: str) -> None:
        """Dibuja líneas de nivel de la función objetivo."""
        coeffs = graphical_result.get("objective_coefficients", {})
        if coeffs.get(x_name) == 0 and coeffs.get(y_name) == 0:
            return
        
        cx, cy, z_opt = coeffs.get(x_name, 0), coeffs.get(y_name, 0), \
                        graphical_result.get("objective_value", 0)
        
        if abs(cy) > _TOL:
            for z_val in [z_opt * 0.5, z_opt * 0.75, z_opt]:
                is_opt = abs(z_val - z_opt) < 1e-6
                ax.plot(x_range, (z_val - cx*x_range)/cy, 'r' + ('-' if is_opt else '--'),
                       linewidth=2.5 if is_opt else 1, alpha=0.8 if is_opt else 0.3,
                       label=f'z={z_val:.2f}' if is_opt else '')

    def _configure_axes(self, ax, x_lim: Tuple, y_lim: Tuple, 
                       x_name: str, y_name: str, is_max: bool) -> None:
        """Configura ejes, límites, título y leyenda."""
        ax.set_xlim(x_lim)
        ax.set_ylim(y_lim)
        ax.set_xlabel(x_name, fontsize=12, fontweight='bold')
        ax.set_ylabel(y_name, fontsize=12, fontweight='bold')
        ax.set_title(f"Método Gráfico - {'Maximización' if is_max else 'Minimización'}",
                    fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=10, framealpha=0.95)
        ax.grid(True, alpha=0.3, linestyle='--')

    def _sort_vertices(self, vertices: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Ordena vértices por ángulo respecto al centroide."""
        if not vertices:
            return vertices
        cx = sum(v[0] for v in vertices) / len(vertices)
        cy = sum(v[1] for v in vertices) / len(vertices)
        return sorted(vertices, key=lambda v: np.arctan2(v[1] - cy, v[0] - cx))

    def _figure_to_base64(self, fig) -> str:
        """Convierte figura matplotlib a PNG base64."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img64 = base64.b64encode(buf.getvalue()).decode()
        buf.close()
        return f"data:image/png;base64,{img64}"

    def _generate_vertices_table(self, feasible_points: List[Dict]) -> List[Dict[str, Any]]:
        """Genera tabla de vértices."""
        return [{"index": i, "x": round(p["point"][0], _PRECISION),
                "y": round(p["point"][1], _PRECISION), "z": round(p["objective"], _PRECISION),
                "is_optimal": p.get("is_optimal", False),
                "status": "✓ ÓPTIMO" if p.get("is_optimal") else ""}
               for i, p in enumerate(feasible_points, 1)]

    def _generate_solution_block(self, graphical_result: Dict, 
                                model: 'MathematicalModel') -> Dict[str, Any]:
        """Genera bloque de solución."""
        var_names = list(model.variables.keys())
        opt_pt = graphical_result.get("optimal_point", (0, 0))
        obj_val = graphical_result.get("objective_value", 0)
        is_max = model.objective == "max"
        return {
            "title": "SOLUCIÓN ÓPTIMA",
            "objective_type": "Maximización" if is_max else "Minimización",
            "variables": {vn: round(opt_pt[i], _PRECISION) for i, vn in enumerate(var_names)},
            "objective_value": round(obj_val, _PRECISION),
            "explanation": graphical_result.get("explanation", "")
        }

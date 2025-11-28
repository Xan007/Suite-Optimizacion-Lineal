"""
Test del análisis de sensibilidad post-óptimo.

Este script prueba el análisis de sensibilidad para los métodos Simplex, Simplex Dual y Gran M.
"""

import sys
import json
sys.path.insert(0, '.')

from app.schemas.analyze_schema import MathematicalModel
from app.services.solver_service import SolverService


def print_separator():
    print("\n" + "=" * 80 + "\n")


def test_simplex_sensitivity():
    """Test de análisis de sensibilidad con método Simplex (maximización)."""
    print("📊 TEST 1: Análisis de Sensibilidad - Método Simplex")
    print_separator()
    
    # Problema clásico de maximización
    # Max Z = 3x₁ + 2x₂
    # s.a. 2x₁ + x₂ ≤ 18
    #      2x₁ + 3x₂ ≤ 42
    #      3x₁ + x₂ ≤ 24
    #      x₁, x₂ ≥ 0
    
    model = MathematicalModel(
        objective_function="3*x1 + 2*x2",
        constraints=[
            "2*x1 + x2 <= 18",
            "2*x1 + 3*x2 <= 42",
            "3*x1 + x2 <= 24",
            "x1 >= 0",
            "x2 >= 0"
        ],
        variables={
            "x1": "Unidades del producto 1",
            "x2": "Unidades del producto 2"
        },
        objective="max"
    )
    
    solver = SolverService()
    result = solver.solve(model, method="simplex")
    
    print(f"✅ Solución exitosa: {result.get('success')}")
    print(f"📈 Valor óptimo: Z = {result.get('objective_value')}")
    print(f"📍 Variables: {result.get('variables')}")
    
    # Verificar análisis de sensibilidad
    sensitivity = result.get("sensitivity_analysis")
    if sensitivity:
        print("\n🔬 ANÁLISIS DE SENSIBILIDAD:")
        print_separator()
        
        # Rangos de optimalidad
        print("📐 RANGOS DE OPTIMALIDAD (Coeficientes de la Función Objetivo):")
        for r in sensitivity.get("objective_ranges", []):
            print(f"\n  Variable: {r['variable']}")
            print(f"  Valor actual: {r['current_value']}")
            print(f"  Rango: [{r['lower_bound_display']}, {r['upper_bound_display']}]")
            print(f"  Decremento permitido: {r['allowable_decrease_display']}")
            print(f"  Incremento permitido: {r['allowable_increase_display']}")
            print(f"  → {r['interpretation']}")
        
        # Precios sombra
        print("\n💰 PRECIOS SOMBRA (Valores Duales):")
        for sp in sensitivity.get("shadow_prices", []):
            status = "ACTIVA (binding)" if sp["binding"] else "NO ACTIVA (holgura)"
            print(f"\n  {sp['constraint_name']}: π = {sp['value']:.4g} [{status}]")
            print(f"  → {sp['economic_interpretation']}")
        
        # Costos reducidos
        print("\n📉 COSTOS REDUCIDOS:")
        for rc in sensitivity.get("reduced_costs", []):
            status = "BÁSICA" if rc["is_basic"] else "NO BÁSICA"
            print(f"\n  {rc['variable']}: c̄ = {rc['value']:.4g} [{status}]")
            print(f"  → {rc['interpretation']}")
        
        # Insights prácticos
        print("\n💡 INSIGHTS PRÁCTICOS:")
        for insight in sensitivity.get("practical_insights", []):
            print(f"  {insight}")
    else:
        print("⚠️ No se generó análisis de sensibilidad")
    
    return result


def test_dual_simplex_sensitivity():
    """Test de análisis de sensibilidad con método Simplex Dual (minimización)."""
    print_separator()
    print("📊 TEST 2: Análisis de Sensibilidad - Método Simplex Dual")
    print_separator()
    
    # Problema de minimización con restricciones >=
    # Min Z = 2x₁ + 3x₂
    # s.a. x₁ + x₂ >= 4
    #      2x₁ + x₂ >= 6
    #      x₁, x₂ >= 0
    
    model = MathematicalModel(
        objective_function="2*x1 + 3*x2",
        constraints=[
            "x1 + x2 >= 4",
            "2*x1 + x2 >= 6",
            "x1 >= 0",
            "x2 >= 0"
        ],
        variables={
            "x1": "Cantidad de recurso 1",
            "x2": "Cantidad de recurso 2"
        },
        objective="min"
    )
    
    solver = SolverService()
    result = solver.solve(model, method="dual_simplex")
    
    print(f"✅ Solución exitosa: {result.get('success')}")
    print(f"📉 Valor óptimo: Z = {result.get('objective_value')}")
    print(f"📍 Variables: {result.get('variables')}")
    
    # Verificar análisis de sensibilidad
    sensitivity = result.get("sensitivity_analysis")
    if sensitivity:
        print("\n🔬 ANÁLISIS DE SENSIBILIDAD:")
        
        # Precios sombra
        print("\n💰 PRECIOS SOMBRA:")
        for sp in sensitivity.get("shadow_prices", []):
            status = "ACTIVA" if sp["binding"] else "NO ACTIVA"
            print(f"  {sp['constraint_name']}: π = {sp['value']:.4g} [{status}]")
        
        # Insights
        print("\n💡 INSIGHTS:")
        for insight in sensitivity.get("practical_insights", []):
            print(f"  {insight}")
    else:
        print("⚠️ No se generó análisis de sensibilidad")
    
    return result


def test_big_m_sensitivity():
    """Test de análisis de sensibilidad con método Gran M."""
    print_separator()
    print("📊 TEST 3: Análisis de Sensibilidad - Método Gran M")
    print_separator()
    
    # Problema con restricciones mixtas
    # Min Z = 4x₁ + x₂
    # s.a. 3x₁ + x₂ = 3
    #      4x₁ + 3x₂ >= 6
    #      x₁ + 2x₂ <= 4
    #      x₁, x₂ >= 0
    
    model = MathematicalModel(
        objective_function="4*x1 + x2",
        constraints=[
            "3*x1 + x2 = 3",
            "4*x1 + 3*x2 >= 6",
            "x1 + 2*x2 <= 4",
            "x1 >= 0",
            "x2 >= 0"
        ],
        variables={
            "x1": "Variable de decisión 1",
            "x2": "Variable de decisión 2"
        },
        objective="min"
    )
    
    solver = SolverService()
    result = solver.solve(model, method="big_m")
    
    print(f"✅ Solución exitosa: {result.get('success')}")
    if result.get('success'):
        print(f"📉 Valor óptimo: Z = {result.get('objective_value')}")
        print(f"📍 Variables: {result.get('variables')}")
        
        sensitivity = result.get("sensitivity_analysis")
        if sensitivity:
            print("\n🔬 ANÁLISIS DE SENSIBILIDAD:")
            
            # Insights
            print("\n💡 INSIGHTS:")
            for insight in sensitivity.get("practical_insights", []):
                print(f"  {insight}")
        else:
            print("⚠️ No se generó análisis de sensibilidad")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    return result


def test_interior_point_no_sensitivity():
    """Verifica que el método de punto interior NO genera análisis de sensibilidad."""
    print_separator()
    print("📊 TEST 4: Verificar que Interior Point NO genera análisis de sensibilidad")
    print_separator()
    
    model = MathematicalModel(
        objective_function="2*x1 + 3*x2",
        constraints=[
            "x1 + x2 >= 4",
            "x1 >= 0",
            "x2 >= 0"
        ],
        variables={
            "x1": "Variable 1",
            "x2": "Variable 2"
        },
        objective="min"
    )
    
    solver = SolverService()
    result = solver.solve(model, method="interior_point")
    
    print(f"✅ Solución exitosa: {result.get('success')}")
    
    sensitivity = result.get("sensitivity_analysis")
    if sensitivity is None:
        print("✅ Correcto: El método de punto interior NO genera análisis de sensibilidad")
    else:
        print("⚠️ Incorrecto: No debería haber análisis de sensibilidad para punto interior")
    
    return result


if __name__ == "__main__":
    print("\n" + "🧪 PRUEBAS DE ANÁLISIS DE SENSIBILIDAD POST-ÓPTIMO 🧪".center(80))
    print("=" * 80)
    
    test_simplex_sensitivity()
    test_dual_simplex_sensitivity()
    test_big_m_sensitivity()
    test_interior_point_no_sensitivity()
    
    print_separator()
    print("✅ Todas las pruebas completadas")

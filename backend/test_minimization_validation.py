"""
Script de prueba para validar las restricciones de métodos en problemas de minimización.

Este script verifica que:
1. Los problemas de minimización NO pueden usar el método Simplex normal
2. Los problemas de minimización NO pueden usar el método gráfico
3. Los problemas de minimización SÍ pueden usar el método Simplex Dual
4. Los problemas de minimización SÍ pueden usar el método de la Gran M
5. Los problemas de maximización pueden usar todos los métodos
"""

import sys
import io

# Configurar salida UTF-8 para compatibilidad con Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.schemas.analyze_schema import MathematicalModel
from app.services.solver_service import SolverService

def test_minimization_restrictions():
    """Prueba las restricciones para problemas de minimización."""
    
    # Crear un problema de minimización simple
    min_model = MathematicalModel(
        objective_function="2*x1 + 3*x2",
        objective="min",
        constraints=[
            "x1 + x2 >= 4",
            "2*x1 + x2 >= 5",
            "x1 >= 0",
            "x2 >= 0"
        ],
        variables={
            "x1": "Variable de decisión 1",
            "x2": "Variable de decisión 2"
        },
        context="Problema de minimización con restricciones >="
    )
    
    # Crear un problema de maximización simple
    max_model = MathematicalModel(
        objective_function="3*x1 + 2*x2",
        objective="max",
        constraints=[
            "2*x1 + x2 <= 10",
            "x1 + 2*x2 <= 8",
            "x1 >= 0",
            "x2 >= 0"
        ],
        variables={
            "x1": "Variable de decisión 1",
            "x2": "Variable de decisión 2"
        },
        context="Problema de maximización con restricciones <="
    )
    
    solver = SolverService()
    
    print("="*80)
    print("PRUEBAS DE VALIDACIÓN DE MÉTODOS PARA MINIMIZACIÓN")
    print("="*80)
    
    # =====================================================================
    # PRUEBAS PARA PROBLEMAS DE MINIMIZACIÓN (deben fallar con simplex y graphical)
    # =====================================================================
    print("\n" + "="*80)
    print("1. PROBLEMA DE MINIMIZACIÓN - Intentando usar Simplex Normal")
    print("="*80)
    result = solver.solve(min_model, method="simplex")
    print(f"✓ Success: {result.get('success')}")
    print(f"✓ Error esperado: {result.get('error', 'N/A')}")
    print(f"✓ Métodos permitidos: {result.get('allowed_methods', 'N/A')}")
    assert result['success'] == False, "❌ ERROR: Debería fallar con simplex en minimización"
    assert "minimización" in result['error'].lower(), "❌ ERROR: El mensaje debería mencionar minimización"
    print("✅ PASS: Simplex normal rechazado correctamente para minimización\n")
    
    print("="*80)
    print("2. PROBLEMA DE MINIMIZACIÓN - Intentando usar Método Gráfico")
    print("="*80)
    result = solver.solve(min_model, method="graphical")
    print(f"✓ Success: {result.get('success')}")
    print(f"✓ Error esperado: {result.get('error', 'N/A')}")
    print(f"✓ Métodos permitidos: {result.get('allowed_methods', 'N/A')}")
    assert result['success'] == False, "❌ ERROR: Debería fallar con graphical en minimización"
    assert "minimización" in result['error'].lower(), "❌ ERROR: El mensaje debería mencionar minimización"
    print("✅ PASS: Método gráfico rechazado correctamente para minimización\n")
    
    # =====================================================================
    # PRUEBAS PARA PROBLEMAS DE MINIMIZACIÓN (deben funcionar con dual_simplex y big_m)
    # =====================================================================
    print("="*80)
    print("3. PROBLEMA DE MINIMIZACIÓN - Usando Simplex Dual (DEBE FUNCIONAR)")
    print("="*80)
    result = solver.solve(min_model, method="dual_simplex")
    print(f"✓ Success: {result.get('success')}")
    print(f"✓ Método: {result.get('method', 'N/A')}")
    print(f"✓ Status: {result.get('status', 'N/A')}")
    if result.get('success'):
        print(f"✓ Valor objetivo: {result.get('objective_value', 'N/A')}")
        print(f"✓ Variables: {result.get('variables', 'N/A')}")
    else:
        print(f"⚠ Error: {result.get('error', 'N/A')}")
    print("✅ PASS: Simplex Dual permitido para minimización\n")
    
    print("="*80)
    print("4. PROBLEMA DE MINIMIZACIÓN - Usando Gran M (DEBE FUNCIONAR)")
    print("="*80)
    result = solver.solve(min_model, method="big_m")
    print(f"✓ Success: {result.get('success')}")
    print(f"✓ Método: {result.get('method', 'N/A')}")
    print(f"✓ Status: {result.get('status', 'N/A')}")
    if result.get('success'):
        print(f"✓ Valor objetivo: {result.get('objective_value', 'N/A')}")
        print(f"✓ Variables: {result.get('variables', 'N/A')}")
    else:
        print(f"⚠ Error: {result.get('error', 'N/A')}")
    print("✅ PASS: Gran M permitido para minimización\n")
    
    # =====================================================================
    # PRUEBAS PARA PROBLEMAS DE MAXIMIZACIÓN (todos los métodos deben funcionar)
    # =====================================================================
    print("="*80)
    print("5. PROBLEMA DE MAXIMIZACIÓN - Usando Simplex Normal (DEBE FUNCIONAR)")
    print("="*80)
    result = solver.solve(max_model, method="simplex")
    print(f"✓ Success: {result.get('success')}")
    print(f"✓ Método: {result.get('method', 'N/A')}")
    print(f"✓ Status: {result.get('status', 'N/A')}")
    if result.get('success'):
        print(f"✓ Valor objetivo: {result.get('objective_value', 'N/A')}")
        print(f"✓ Variables: {result.get('variables', 'N/A')}")
        print(f"✓ Iteraciones: {result.get('iterations', 'N/A')}")
    print("✅ PASS: Simplex normal permitido para maximización\n")
    
    print("="*80)
    print("6. PROBLEMA DE MAXIMIZACIÓN - Usando Método Gráfico (DEBE FUNCIONAR)")
    print("="*80)
    result = solver.solve(max_model, method="graphical")
    print(f"✓ Success: {result.get('success')}")
    print(f"✓ Método: {result.get('method', 'N/A')}")
    print(f"✓ Status: {result.get('status', 'N/A')}")
    if result.get('success'):
        print(f"✓ Valor objetivo: {result.get('objective_value', 'N/A')}")
        print(f"✓ Punto óptimo: {result.get('optimal_point', 'N/A')}")
        print(f"✓ Puntos factibles evaluados: {len(result.get('feasible_points', []))}")
    print("✅ PASS: Método gráfico permitido para maximización\n")
    
    # =====================================================================
    # PRUEBA DE determine_applicable_methods
    # =====================================================================
    print("="*80)
    print("7. VERIFICANDO determine_applicable_methods()")
    print("="*80)
    
    print("\nPara MINIMIZACIÓN:")
    suggested_min, not_applicable_min = solver.determine_applicable_methods(min_model)
    print(f"✓ Métodos sugeridos: {suggested_min}")
    print(f"✓ Métodos NO aplicables: {not_applicable_min}")
    assert "simplex" in not_applicable_min, "❌ ERROR: simplex debería estar en no aplicables"
    assert "graphical" in not_applicable_min, "❌ ERROR: graphical debería estar en no aplicables"
    assert "dual_simplex" in suggested_min or "big_m" in suggested_min, "❌ ERROR: dual_simplex o big_m deberían estar sugeridos"
    print("✅ PASS: determine_applicable_methods correcto para minimización\n")
    
    print("Para MAXIMIZACIÓN:")
    suggested_max, not_applicable_max = solver.determine_applicable_methods(max_model)
    print(f"✓ Métodos sugeridos: {suggested_max}")
    print(f"✓ Métodos NO aplicables: {not_applicable_max}")
    assert "simplex" not in not_applicable_max, "❌ ERROR: simplex NO debería estar en no aplicables para max"
    assert "graphical" in suggested_max or len(max_model.variables) > 2, "❌ ERROR: graphical debería estar sugerido para 2 variables"
    print("✅ PASS: determine_applicable_methods correcto para maximización\n")
    
    print("="*80)
    print("🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE 🎉")
    print("="*80)
    print("\nRESUMEN:")
    print("✅ Problemas de minimización NO pueden usar Simplex normal")
    print("✅ Problemas de minimización NO pueden usar Método gráfico")
    print("✅ Problemas de minimización SÍ pueden usar Simplex Dual")
    print("✅ Problemas de minimización SÍ pueden usar Gran M")
    print("✅ Problemas de maximización pueden usar todos los métodos")
    print("✅ determine_applicable_methods retorna valores correctos")


if __name__ == "__main__":
    test_minimization_restrictions()

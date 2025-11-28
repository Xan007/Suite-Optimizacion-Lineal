"""
Script de prueba para el método Simplex Dual.

Este script demuestra el uso del método Simplex Dual para problemas de minimización
con restricciones >=. Muestra la visualización HTML con colores para pivotes.
"""

import json
from app.services.dual_simplex_method import DualSimplexMethod
from app.services.dual_simplex_visualizer import DualSimplexVisualizer
from app.schemas.analyze_schema import MathematicalModel


def test_dual_simplex_basic():
    """
    Prueba básica del Simplex Dual con un problema de minimización simple.
    
    Problema:
    Minimizar: z = 2*x1 + 3*x2
    Sujeto a:
        x1 + x2 >= 4
        2*x1 + x2 >= 5
        x1, x2 >= 0
    """
    print("=" * 80)
    print("PRUEBA 1: Problema de Minimización con Restricciones >=")
    print("=" * 80)
    
    model = MathematicalModel(
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
    
    # Resolver con Simplex Dual
    solver = DualSimplexMethod()
    result = solver.solve(model)
    
    # Mostrar resultados
    print(f"\n✅ Éxito: {result.get('success')}")
    print(f"Estado: {result.get('status')}")
    print(f"Valor Óptimo: {result.get('objective_value')}")
    print(f"Solución: {result.get('variables')}")
    print(f"Iteraciones: {result.get('iterations')}")
    
    # Mostrar pasos
    print("\n📊 PASOS DE ITERACIÓN:")
    for i, step in enumerate(result.get('steps', [])):
        print(f"\n--- Iteración {step['iteration']} ---")
        print(f"Descripción: {step['description']}")
        if step.get('entering_variable'):
            print(f"  Entra: {step['entering_variable']}")
            print(f"  Sale: {step['leaving_variable']}")
            print(f"  Pivote: fila {step['pivot_row']}, columna {step['pivot_column']}")
            print(f"  Elemento pivote: {step['pivot_element']}")
        print(f"  ¿Factible?: {step.get('is_feasible', False)}")
    
    # Generar visualización HTML
    if result.get('steps'):
        visualizer = DualSimplexVisualizer()
        html = visualizer.generate_html_visualization(result['steps'])
        
        # Guardar HTML
        with open('dual_simplex_test1.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n💾 Visualización HTML guardada en: dual_simplex_test1.html")
    
    print("\n" + "=" * 80)


def test_dual_simplex_complex():
    """
    Prueba con un problema más complejo.
    
    Problema:
    Minimizar: z = 3*x1 + 2*x2 + 4*x3
    Sujeto a:
        x1 + x2 + x3 >= 5
        2*x1 + x2 >= 4
        x1 + 3*x2 >= 6
        x1, x2, x3 >= 0
    """
    print("=" * 80)
    print("PRUEBA 2: Problema con 3 Variables y Múltiples Restricciones >=")
    print("=" * 80)
    
    model = MathematicalModel(
        objective_function="3*x1 + 2*x2 + 4*x3",
        objective="min",
        constraints=[
            "x1 + x2 + x3 >= 5",
            "2*x1 + x2 >= 4",
            "x1 + 3*x2 >= 6",
            "x1 >= 0",
            "x2 >= 0",
            "x3 >= 0"
        ],
        variables={
            "x1": "Variable de decisión 1",
            "x2": "Variable de decisión 2",
            "x3": "Variable de decisión 3"
        },
        context="Problema de minimización con 3 variables"
    )
    
    # Resolver con Simplex Dual
    solver = DualSimplexMethod()
    result = solver.solve(model)
    
    # Mostrar resultados
    print(f"\n✅ Éxito: {result.get('success')}")
    print(f"Estado: {result.get('status')}")
    print(f"Valor Óptimo: {result.get('objective_value')}")
    print(f"Solución: {result.get('variables')}")
    print(f"Iteraciones: {result.get('iterations')}")
    
    # Generar visualización HTML
    if result.get('steps'):
        visualizer = DualSimplexVisualizer()
        html = visualizer.generate_html_visualization(result['steps'])
        
        # Guardar HTML
        with open('dual_simplex_test2.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n💾 Visualización HTML guardada en: dual_simplex_test2.html")
    
    print("\n" + "=" * 80)


def test_dual_simplex_infeasible():
    """
    Prueba con un problema infactible.
    
    Problema:
    Minimizar: z = x1 + x2
    Sujeto a:
        x1 + x2 >= 5
        x1 + x2 <= 3
        x1, x2 >= 0
    """
    print("=" * 80)
    print("PRUEBA 3: Problema Infactible")
    print("=" * 80)
    
    model = MathematicalModel(
        objective_function="x1 + x2",
        objective="min",
        constraints=[
            "x1 + x2 >= 5",
            "x1 + x2 <= 3",
            "x1 >= 0",
            "x2 >= 0"
        ],
        variables={
            "x1": "Variable de decisión 1",
            "x2": "Variable de decisión 2"
        },
        context="Problema infactible"
    )
    
    # Resolver con Simplex Dual
    solver = DualSimplexMethod()
    result = solver.solve(model)
    
    # Mostrar resultados
    print(f"\n✅ Éxito: {result.get('success')}")
    print(f"Estado: {result.get('status')}")
    print(f"Error: {result.get('error', 'N/A')}")
    print(f"Iteraciones: {result.get('iterations')}")
    
    # Generar visualización HTML (incluso para infactibles)
    if result.get('steps'):
        visualizer = DualSimplexVisualizer()
        html = visualizer.generate_html_visualization(result['steps'])
        
        # Guardar HTML
        with open('dual_simplex_test3_infeasible.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n💾 Visualización HTML guardada en: dual_simplex_test3_infeasible.html")
    
    print("\n" + "=" * 80)


def test_solver_service_integration():
    """
    Prueba la integración con SolverService.
    """
    print("=" * 80)
    print("PRUEBA 4: Integración con SolverService")
    print("=" * 80)
    
    from app.services.solver_service import SolverService
    
    model = MathematicalModel(
        objective_function="4*x1 + 3*x2",
        objective="min",
        constraints=[
            "2*x1 + x2 >= 10",
            "x1 + 2*x2 >= 8",
            "x1 >= 0",
            "x2 >= 0"
        ],
        variables={
            "x1": "Cantidad de producto 1",
            "x2": "Cantidad de producto 2"
        },
        context="Problema de producción con costos mínimos"
    )
    
    solver_service = SolverService()
    
    # Determinar métodos aplicables
    suggested, not_applicable = solver_service.determine_applicable_methods(model)
    print(f"\n✅ Métodos sugeridos: {suggested}")
    print(f"❌ Métodos no aplicables: {not_applicable}")
    
    # Resolver con Simplex Dual
    result = solver_service.solve(model, method="dual_simplex")
    
    print(f"\n✅ Éxito: {result.get('success')}")
    print(f"Método usado: {result.get('method')}")
    print(f"Valor Óptimo: {result.get('objective_value')}")
    print(f"Solución: {result.get('variables')}")
    
    # Verificar que se generó la visualización HTML
    if result.get('html_visualization'):
        with open('dual_simplex_test4_service.html', 'w', encoding='utf-8') as f:
            f.write(result['html_visualization'])
        print(f"\n💾 Visualización HTML guardada en: dual_simplex_test4_service.html")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🚀 INICIANDO PRUEBAS DEL MÉTODO SIMPLEX DUAL\n")
    
    # Ejecutar todas las pruebas
    test_dual_simplex_basic()
    print("\n")
    
    test_dual_simplex_complex()
    print("\n")
    
    test_dual_simplex_infeasible()
    print("\n")
    
    test_solver_service_integration()
    
    print("\n✅ TODAS LAS PRUEBAS COMPLETADAS\n")
    print("📁 Se han generado archivos HTML con visualizaciones detalladas.")
    print("   Abre los archivos .html en tu navegador para ver las tablas con colores.")

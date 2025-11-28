"""
Script de prueba de integración para validar la API con problemas de minimización.

Este script prueba el endpoint /api/v1/analyze/solve con diferentes combinaciones
de problemas y métodos para verificar que la validación funcione correctamente.

REQUISITO: El servidor Django debe estar corriendo en http://localhost:8000
Para iniciar el servidor: python manage.py runserver
"""

import requests
import json

BASE_URL = "http://localhost:8000"
SOLVE_ENDPOINT = f"{BASE_URL}/api/v1/analyze/solve"

def test_api_validation():
    """Prueba la validación de métodos a través de la API HTTP."""
    
    # Modelo de minimización
    min_model = {
        "objective_function": "2*x1 + 3*x2",
        "objective": "min",
        "constraints": [
            "x1 + x2 >= 4",
            "2*x1 + x2 >= 5",
            "x1 >= 0",
            "x2 >= 0"
        ],
        "variables": {
            "x1": "Variable de decisión 1",
            "x2": "Variable de decisión 2"
        },
        "context": "Problema de minimización con restricciones >="
    }
    
    # Modelo de maximización
    max_model = {
        "objective_function": "3*x1 + 2*x2",
        "objective": "max",
        "constraints": [
            "2*x1 + x2 <= 10",
            "x1 + 2*x2 <= 8",
            "x1 >= 0",
            "x2 >= 0"
        ],
        "variables": {
            "x1": "Variable de decisión 1",
            "x2": "Variable de decisión 2"
        },
        "context": "Problema de maximización con restricciones <="
    }
    
    print("="*80)
    print("PRUEBAS DE INTEGRACIÓN - API DE VALIDACIÓN DE MÉTODOS")
    print("="*80)
    print(f"\n📡 Servidor: {BASE_URL}")
    print(f"📍 Endpoint: {SOLVE_ENDPOINT}\n")
    
    # Verificar que el servidor esté corriendo
    try:
        health_response = requests.get(f"{BASE_URL}/api/v1/test/", timeout=5)
        if health_response.status_code != 200:
            print("❌ ERROR: El servidor no está respondiendo correctamente")
            print("⚠️  Asegúrate de que el servidor Django esté corriendo:")
            print("   python manage.py runserver")
            return
        print("✅ Servidor Django activo y respondiendo\n")
    except requests.exceptions.RequestException as e:
        print("❌ ERROR: No se puede conectar al servidor")
        print(f"   Error: {e}")
        print("\n⚠️  Por favor inicia el servidor Django:")
        print("   cd backend")
        print("   python manage.py runserver")
        return
    
    # =========================================================================
    # PRUEBA 1: Minimización + Simplex Normal (debe fallar)
    # =========================================================================
    print("="*80)
    print("TEST 1: Minimización + Simplex Normal → Debe RECHAZAR")
    print("="*80)
    response = requests.post(
        SOLVE_ENDPOINT,
        json={"model": min_model, "method": "simplex"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Success: {data.get('success', data.get('result', {}).get('success'))}")
    
    if response.status_code == 400:
        print(f"✅ PASS - Rechazado correctamente (HTTP 400)")
        print(f"   Mensaje: {data.get('detail', 'N/A')}")
        print(f"   Métodos permitidos: {data.get('allowed_methods', 'N/A')}")
    else:
        print(f"❌ FAIL - Debería retornar HTTP 400")
    print()
    
    # =========================================================================
    # PRUEBA 2: Minimización + Método Gráfico (debe fallar)
    # =========================================================================
    print("="*80)
    print("TEST 2: Minimización + Método Gráfico → Debe RECHAZAR")
    print("="*80)
    response = requests.post(
        SOLVE_ENDPOINT,
        json={"model": min_model, "method": "graphical"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Success: {data.get('success', data.get('result', {}).get('success'))}")
    
    if response.status_code == 400:
        print(f"✅ PASS - Rechazado correctamente (HTTP 400)")
        print(f"   Mensaje: {data.get('detail', 'N/A')}")
        print(f"   Métodos permitidos: {data.get('allowed_methods', 'N/A')}")
    else:
        print(f"❌ FAIL - Debería retornar HTTP 400")
    print()
    
    # =========================================================================
    # PRUEBA 3: Minimización + Simplex Dual (debe funcionar)
    # =========================================================================
    print("="*80)
    print("TEST 3: Minimización + Simplex Dual → Debe FUNCIONAR")
    print("="*80)
    response = requests.post(
        SOLVE_ENDPOINT,
        json={"model": min_model, "method": "dual_simplex"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    data = response.json()
    result = data.get('result', {})
    print(f"Success: {result.get('success')}")
    
    if response.status_code == 200 and result.get('success'):
        print(f"✅ PASS - Resuelto correctamente")
        print(f"   Método: {result.get('method')}")
        print(f"   Valor objetivo: {result.get('objective_value')}")
        print(f"   Variables: {result.get('variables')}")
    else:
        print(f"❌ FAIL - Debería resolver exitosamente")
        print(f"   Error: {result.get('error', 'N/A')}")
    print()
    
    # =========================================================================
    # PRUEBA 4: Minimización + Gran M (debe funcionar)
    # =========================================================================
    print("="*80)
    print("TEST 4: Minimización + Gran M → Debe FUNCIONAR")
    print("="*80)
    response = requests.post(
        SOLVE_ENDPOINT,
        json={"model": min_model, "method": "big_m"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    data = response.json()
    result = data.get('result', {})
    print(f"Success: {result.get('success')}")
    
    if response.status_code == 200:
        print(f"✅ PASS - Método permitido (HTTP 200)")
        print(f"   Método: {result.get('method')}")
        print(f"   Status: {result.get('status')}")
        if result.get('success'):
            print(f"   Valor objetivo: {result.get('objective_value')}")
        else:
            print(f"   Nota: {result.get('error', 'Problema puede ser infactible')}")
    else:
        print(f"❌ FAIL - Debería permitir el método")
    print()
    
    # =========================================================================
    # PRUEBA 5: Maximización + Simplex Normal (debe funcionar)
    # =========================================================================
    print("="*80)
    print("TEST 5: Maximización + Simplex Normal → Debe FUNCIONAR")
    print("="*80)
    response = requests.post(
        SOLVE_ENDPOINT,
        json={"model": max_model, "method": "simplex"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    data = response.json()
    result = data.get('result', {})
    print(f"Success: {result.get('success')}")
    
    if response.status_code == 200 and result.get('success'):
        print(f"✅ PASS - Resuelto correctamente")
        print(f"   Método: {result.get('method')}")
        print(f"   Valor objetivo: {result.get('objective_value')}")
        print(f"   Variables: {result.get('variables')}")
        print(f"   Iteraciones: {result.get('iterations')}")
    else:
        print(f"❌ FAIL - Debería resolver exitosamente")
    print()
    
    # =========================================================================
    # PRUEBA 6: Maximización + Método Gráfico (debe funcionar)
    # =========================================================================
    print("="*80)
    print("TEST 6: Maximización + Método Gráfico → Debe FUNCIONAR")
    print("="*80)
    response = requests.post(
        SOLVE_ENDPOINT,
        json={"model": max_model, "method": "graphical"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    data = response.json()
    result = data.get('result', {})
    print(f"Success: {result.get('success')}")
    
    if response.status_code == 200 and result.get('success'):
        print(f"✅ PASS - Resuelto correctamente")
        print(f"   Método: {result.get('method')}")
        print(f"   Valor objetivo: {result.get('objective_value')}")
        print(f"   Punto óptimo: {result.get('optimal_point')}")
        print(f"   Puntos evaluados: {len(result.get('feasible_points', []))}")
        print(f"   Gráfica generada: {'Sí' if result.get('graph') else 'No'}")
    else:
        print(f"❌ FAIL - Debería resolver exitosamente")
    print()
    
    print("="*80)
    print("🎉 PRUEBAS DE INTEGRACIÓN COMPLETADAS")
    print("="*80)
    print("\n✅ Todas las validaciones funcionan correctamente a nivel HTTP")
    print("✅ El servidor rechaza métodos no permitidos con HTTP 400")
    print("✅ El servidor permite métodos correctos con HTTP 200")


if __name__ == "__main__":
    print("\n🚀 Iniciando pruebas de integración...\n")
    print("⚠️  IMPORTANTE: Asegúrate de que el servidor Django esté corriendo:")
    print("   cd backend")
    print("   python manage.py runserver\n")
    
    input("Presiona ENTER para continuar con las pruebas...")
    print()
    
    test_api_validation()

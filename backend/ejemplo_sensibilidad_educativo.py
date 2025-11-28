"""
Ejemplo educativo de Análisis de Sensibilidad Post-Óptimo

Este archivo demuestra el análisis de sensibilidad completo usando
un problema clásico de programación lineal con interpretación económica.

PROBLEMA: Fábrica de Muebles
============================
Una fábrica produce sillas y mesas. 
- Cada silla requiere 4 horas de trabajo y 2 unidades de madera, con ganancia de $70
- Cada mesa requiere 6 horas de trabajo y 3 unidades de madera, con ganancia de $120

Recursos disponibles:
- 120 horas de trabajo
- 72 unidades de madera

Objetivo: Maximizar la ganancia total.
"""

import sys
sys.path.insert(0, '.')

from app.schemas.analyze_schema import MathematicalModel
from app.services.solver_service import SolverService


def main():
    print("\n" + "="*80)
    print("📚 ANÁLISIS DE SENSIBILIDAD POST-ÓPTIMO - EJEMPLO DIDÁCTICO")
    print("="*80)
    
    print("""
    
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    PROBLEMA: FÁBRICA DE MUEBLES                  ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║  Una fábrica produce SILLAS y MESAS:                            ║
    ║                                                                  ║
    ║  • Silla: 4h trabajo, 2 unidades madera → Ganancia: $70         ║
    ║  • Mesa:  6h trabajo, 3 unidades madera → Ganancia: $120        ║
    ║                                                                  ║
    ║  Recursos disponibles:                                           ║
    ║  • Trabajo: 120 horas                                            ║
    ║  • Madera:  72 unidades                                          ║
    ║                                                                  ║
    ║  OBJETIVO: Maximizar ganancia total                              ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Definir el modelo
    model = MathematicalModel(
        objective_function="70*x1 + 120*x2",
        constraints=[
            "4*x1 + 6*x2 <= 120",   # Horas de trabajo
            "2*x1 + 3*x2 <= 72",    # Unidades de madera
            "x1 >= 0",
            "x2 >= 0"
        ],
        variables={
            "x1": "Número de sillas a producir",
            "x2": "Número de mesas a producir"
        },
        objective="max",
        context="Problema de producción de muebles"
    )
    
    print("\n📐 FORMULACIÓN MATEMÁTICA:")
    print("-"*40)
    print("   Maximizar  Z = 70x₁ + 120x₂")
    print("\n   Sujeto a:")
    print("   4x₁ + 6x₂ ≤ 120  (Horas de trabajo)")
    print("   2x₁ + 3x₂ ≤ 72   (Unidades de madera)")
    print("   x₁, x₂ ≥ 0       (No negatividad)")
    
    # Resolver
    solver = SolverService()
    result = solver.solve(model, method="simplex")
    
    print("\n\n" + "="*80)
    print("📊 SOLUCIÓN ÓPTIMA")
    print("="*80)
    
    if result.get("success"):
        print(f"""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                      RESULTADOS ÓPTIMOS                          ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║  • Sillas a producir (x₁):  {result['variables']['x1']:.0f}                            ║
    ║  • Mesas a producir (x₂):   {result['variables']['x2']:.0f}                            ║
    ║                                                                  ║
    ║  📈 GANANCIA MÁXIMA: ${result['objective_value']:.0f}                                 ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
        """)
        
        # Análisis de sensibilidad
        sensitivity = result.get("sensitivity_analysis")
        if sensitivity:
            print("\n" + "="*80)
            print("🔬 ANÁLISIS DE SENSIBILIDAD POST-ÓPTIMO")
            print("="*80)
            
            # Explicación teórica
            print("""
    ┌────────────────────────────────────────────────────────────────────┐
    │                    ¿QUÉ ES EL ANÁLISIS DE SENSIBILIDAD?           │
    ├────────────────────────────────────────────────────────────────────┤
    │                                                                    │
    │  El análisis de sensibilidad responde preguntas como:             │
    │                                                                    │
    │  1. ¿Cuánto podemos variar los precios/costos sin cambiar         │
    │     qué productos fabricar?                                        │
    │                                                                    │
    │  2. ¿Cuánto vale una hora extra de trabajo? (Precio sombra)       │
    │                                                                    │
    │  3. ¿Qué recurso debemos aumentar primero?                        │
    │                                                                    │
    └────────────────────────────────────────────────────────────────────┘
            """)
            
            # Rangos de optimalidad
            print("\n📐 RANGOS DE OPTIMALIDAD (Coeficientes de la Función Objetivo)")
            print("-"*60)
            print("""
    Estos rangos indican cuánto pueden variar las ganancias por unidad
    sin que cambie LA MEZCLA DE PRODUCTOS ÓPTIMA (qué producir).
    
    NOTA: El valor óptimo Z SÍ cambiará dentro de estos rangos.
            """)
            
            for r in sensitivity.get("objective_ranges", []):
                var_name = "Sillas" if r['variable'] == 'x1' else "Mesas"
                print(f"""
    📦 {var_name} ({r['variable']}):
       • Ganancia actual: ${r['current_value']:.0f} por unidad
       • Rango permitido: [${r['lower_bound_display']}, ${r['upper_bound_display']}]
       • Puede disminuir hasta: ${r['allowable_decrease_display']}
       • Puede aumentar hasta: ${r['allowable_increase_display']}
       
       💡 {r['interpretation']}
                """)
            
            # Precios sombra
            print("\n\n💰 PRECIOS SOMBRA (Valores Duales)")
            print("-"*60)
            print("""
    Los precios sombra indican el VALOR MARGINAL de cada recurso:
    ¿Cuánto aumentaría la ganancia si tuviéramos 1 unidad más?
            """)
            
            constraint_labels = ["Horas de trabajo", "Unidades de madera"]
            for i, sp in enumerate(sensitivity.get("shadow_prices", [])):
                label = constraint_labels[i] if i < len(constraint_labels) else sp['constraint_name']
                binding_status = "ACTIVA (recurso agotado)" if sp['binding'] else "NO ACTIVA (hay sobrante)"
                
                print(f"""
    🏭 {label}:
       • Precio sombra π = ${sp['value']:.2f}
       • Estado: {binding_status}
       
       💡 {sp['economic_interpretation']}
                """)
            
            # Costos reducidos
            print("\n\n📉 COSTOS REDUCIDOS")
            print("-"*60)
            print("""
    Los costos reducidos indican si una variable NO básica (= 0) 
    debería entrar a la solución.
            """)
            
            for rc in sensitivity.get("reduced_costs", []):
                var_name = "Sillas" if rc['variable'] == 'x1' else "Mesas"
                status = "EN PRODUCCIÓN" if rc['is_basic'] else "NO SE PRODUCE"
                
                print(f"""
    📊 {var_name} ({rc['variable']}):
       • Costo reducido: c̄ = {rc['value']:.2f}
       • Estado: {status}
       
       💡 {rc['interpretation']}
                """)
            
            # Insights prácticos
            print("\n\n💡 CONCLUSIONES Y RECOMENDACIONES")
            print("-"*60)
            for insight in sensitivity.get("practical_insights", []):
                print(f"    {insight}")
            
            # Ejemplo de uso práctico
            print("""
            
    ┌────────────────────────────────────────────────────────────────────┐
    │                    EJEMPLO DE APLICACIÓN PRÁCTICA                  │
    ├────────────────────────────────────────────────────────────────────┤
    │                                                                    │
    │  PREGUNTA: ¿Deberíamos contratar más trabajadores o comprar       │
    │            más madera?                                             │
    │                                                                    │
    │  RESPUESTA: Depende de los precios sombra:                        │
    │                                                                    │
    │  - Si π(trabajo) > π(madera): Invertir en más horas de trabajo    │
    │  - Si π(madera) > π(trabajo): Invertir en más madera              │
    │  - Si π = 0: El recurso tiene excedente, no vale la pena más      │
    │                                                                    │
    │  Los precios sombra son válidos SOLO dentro de los rangos         │
    │  de factibilidad del RHS.                                         │
    └────────────────────────────────────────────────────────────────────┘
            """)
    else:
        print(f"❌ Error: {result.get('error')}")
    
    return result


if __name__ == "__main__":
    main()

# ⚡ Quick Start - Método Simplex Dual

## Uso en 3 Pasos

---

## 🚀 Paso 1: Ejecutar el Test

```powershell
cd backend
python test_dual_simplex.py
```

**Resultado esperado:**
```
🚀 INICIANDO PRUEBAS DEL MÉTODO SIMPLEX DUAL

================================================================================
PRUEBA 1: Problema de Minimización con Restricciones >=
================================================================================

✅ Éxito: True
Estado: optimal
Valor Óptimo: 8.0
Solución: {'x1': 4.0, 'x2': 0.0}
Iteraciones: 3

💾 Visualización HTML guardada en: dual_simplex_test1.html
...

✅ TODAS LAS PRUEBAS COMPLETADAS
```

---

## 🌐 Paso 2: Abrir la Visualización

Abre cualquiera de los archivos `.html` generados en tu navegador:

```
dual_simplex_test1.html
dual_simplex_test2.html
dual_simplex_test3_infeasible.html
dual_simplex_test4_service.html
```

**Verás:**
- 🎨 Tablas con colores para pivotes
- 📝 Explicaciones paso a paso
- 📊 Razones duales calculadas
- ✅ Estado de factibilidad en cada iteración

---

## 💻 Paso 3: Usar desde tu Código

### Python:

```python
from app.services.dual_simplex_method import DualSimplexMethod
from app.schemas.analyze_schema import MathematicalModel

# Definir problema
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
        "x1": "Cantidad 1",
        "x2": "Cantidad 2"
    }
)

# Resolver
solver = DualSimplexMethod()
result = solver.solve(model)

# Ver resultado
print(f"Óptimo: {result['objective_value']}")
print(f"x1 = {result['variables']['x1']}")
print(f"x2 = {result['variables']['x2']}")
```

### API (cURL):

```bash
curl -X POST http://localhost:8000/api/v1/analyze/solve \
  -H "Content-Type: application/json" \
  -d '{
    "model": {
      "objective_function": "2*x1 + 3*x2",
      "objective": "min",
      "constraints": ["x1 + x2 >= 4", "2*x1 + x2 >= 5"],
      "variables": {"x1": "Var 1", "x2": "Var 2"}
    },
    "method": "dual_simplex"
  }'
```

---

## 📚 Documentación Completa

| Documento | Descripción |
|-----------|-------------|
| **DUAL_SIMPLEX_README.md** | Guía completa (600 líneas) |
| **API_USAGE_GUIDE.md** | Uso de API (1,000 líneas) |
| **VISUALIZACION_EJEMPLO.md** | Ejemplos visuales (700 líneas) |
| **IMPLEMENTACION_COMPLETADA.md** | Resumen técnico (500 líneas) |
| **RESUMEN_EJECUTIVO.md** | Vista general ejecutiva |

---

## 🎯 Casos de Uso

### 1. Problema de Minimización Simple

```python
# Minimizar: 2x₁ + 3x₂
# Sujeto a: x₁ + x₂ ≥ 4, 2x₁ + x₂ ≥ 5

model = MathematicalModel(
    objective_function="2*x1 + 3*x2",
    objective="min",
    constraints=["x1 + x2 >= 4", "2*x1 + x2 >= 5", "x1 >= 0", "x2 >= 0"],
    variables={"x1": "x1", "x2": "x2"}
)

result = DualSimplexMethod().solve(model)
# Resultado: x1=4.0, x2=0.0, z=8.0
```

### 2. Problema con 3+ Variables

```python
# Minimizar: 3x₁ + 2x₂ + 4x₃
# Múltiples restricciones ≥

model = MathematicalModel(
    objective_function="3*x1 + 2*x2 + 4*x3",
    objective="min",
    constraints=[
        "x1 + x2 + x3 >= 5",
        "2*x1 + x2 >= 4",
        "x1 + 3*x2 >= 6",
        "x1 >= 0", "x2 >= 0", "x3 >= 0"
    ],
    variables={"x1": "x1", "x2": "x2", "x3": "x3"}
)

result = DualSimplexMethod().solve(model)
# Resultado: x1=0.0, x2=5.0, x3=0.0, z=10.0
```

### 3. Con Visualización HTML

```python
from app.services.dual_simplex_visualizer import DualSimplexVisualizer

# Después de resolver...
visualizer = DualSimplexVisualizer()
html = visualizer.generate_html_visualization(result['steps'])

# Guardar
with open('mi_solucion.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Visualización guardada en mi_solucion.html")
```

---

## ⚠️ Requisitos

- Python 3.8+
- NumPy
- SymPy
- Django (para API)

**Ya instalado si tienes el proyecto completo.**

---

## 🎨 Colores en la Visualización

| Color | Elemento | Significado |
|-------|----------|-------------|
| 🔴 Rojo | Elemento pivote | Celda donde ocurre el pivoteo |
| 🌸 Rosa | Fila pivote | Variable que sale de la base |
| 💙 Azul | Columna pivote | Variable que entra a la base |
| 🟠 Naranja | RHS negativo | Solución aún infactible |
| 💜 Púrpura | Variable holgura | Variables agregadas |
| 🟢 Verde | Óptimo | Solución encontrada |

---

## 🆘 Troubleshooting

### Error: "El método Simplex Dual solo se aplica a problemas de minimización"

**Solución:** Cambia `objective="max"` a `objective="min"`

### Error: "Problema infactible"

**Significado:** Las restricciones son contradictorias. Ejemplo:
```
x1 + x2 >= 5  y  x1 + x2 <= 3
```

### Visualización no se genera

**Verifica:** 
```python
if result.get('steps'):
    # Hay pasos para visualizar
else:
    print("No hay pasos disponibles")
```

---

## 📞 Ayuda

Consulta la documentación completa en:

- **Algoritmo**: `DUAL_SIMPLEX_README.md`
- **API**: `API_USAGE_GUIDE.md`
- **Visualización**: `VISUALIZACION_EJEMPLO.md`

---

**¡Listo para usar! 🎉**

Ejecuta `python test_dual_simplex.py` y explora los archivos HTML generados.

# Método Simplex Dual - Documentación Completa

## 📋 Índice

1. [Descripción General](#descripción-general)
2. [Características](#características)
3. [Cuándo Usar Simplex Dual](#cuándo-usar-simplex-dual)
4. [Uso del Sistema](#uso-del-sistema)
5. [Algoritmo y Lógica](#algoritmo-y-lógica)
6. [Visualización Gráfica](#visualización-gráfica)
7. [Ejemplos](#ejemplos)

---

## 🎯 Descripción General

El **método Simplex Dual** es un algoritmo para resolver problemas de programación lineal que comienza con una solución dual-factible pero primal-infactible. Es particularmente útil para problemas de **minimización con restricciones ≥**.

### Diferencias con Simplex Primal

| Característica | Simplex Primal | Simplex Dual |
|----------------|----------------|--------------|
| Factibilidad inicial | Primal-factible (RHS ≥ 0) | Dual-factible (coef. Z ≥ 0) |
| Tipo de problema | Maximización con ≤ | Minimización con ≥ |
| Selección de fila | Razón mínima (RHS/coef) | RHS más negativo |
| Selección de columna | Coeficiente más negativo en Z | Razón dual mínima |
| Criterio de parada | Todos coef. Z ≥ 0 | Todos RHS ≥ 0 |

---

## ✨ Características

### 1. **Implementación Orientada a Objetos**
- Clase `DualSimplexMethod` con lógica del algoritmo
- Clase `DualSimplexVisualizer` para generación de visualizaciones
- Separación clara de responsabilidades

### 2. **Visualización Gráfica Detallada**
- **Tablas HTML con colores**:
  - 🔴 Rojo: Elemento pivote
  - 🌸 Rosa: Fila pivote (variable saliente)
  - 💙 Azul: Columna pivote (variable entrante)
  - 🟠 Naranja: RHS negativos
  - 💜 Púrpura: Variables de holgura

### 3. **Explicaciones Paso a Paso**
- Descripción de cada iteración
- Cálculo de razones duales mostrado en tablas
- Estado de factibilidad en cada paso
- Variables de holgura identificadas claramente

### 4. **Manejo de Casos Especiales**
- ✅ Soluciones óptimas
- ❌ Problemas infactibles
- ⚠️ Detección de ciclado (máximo 1000 iteraciones)

---

## 🔍 Cuándo Usar Simplex Dual

### Casos de Uso Principales

1. **Problemas de Minimización con Restricciones ≥**
   ```
   Minimizar: z = c₁x₁ + c₂x₂ + ...
   Sujeto a:
       a₁₁x₁ + a₁₂x₂ + ... ≥ b₁
       a₂₁x₁ + a₂₂x₂ + ... ≥ b₂
       x₁, x₂, ... ≥ 0
   ```

2. **Post-Optimización**
   - Agregar nuevas restricciones a un problema ya resuelto
   - La solución anterior puede volverse infactible

3. **Análisis de Sensibilidad**
   - Cambios en los RHS de restricciones
   - Evaluar impacto sin resolver desde cero

### El Sistema Detecta Automáticamente

El `SolverService` identifica automáticamente cuándo usar Simplex Dual:

```python
suggested_methods = ["dual_simplex", "big_m", "simplex", "graphical"]
```

---

## 🚀 Uso del Sistema

### 1. Desde Python (Directo)

```python
from app.services.dual_simplex_method import DualSimplexMethod
from app.schemas.analyze_schema import MathematicalModel

# Definir el problema
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
    }
)

# Resolver
solver = DualSimplexMethod()
result = solver.solve(model)

# Ver resultados
print(f"Valor óptimo: {result['objective_value']}")
print(f"Solución: {result['variables']}")
print(f"Iteraciones: {result['iterations']}")
```

### 2. Con Visualización HTML

```python
from app.services.dual_simplex_visualizer import DualSimplexVisualizer

# Después de resolver...
if result.get('steps'):
    visualizer = DualSimplexVisualizer()
    html = visualizer.generate_html_visualization(result['steps'])
    
    # Guardar archivo
    with open('solucion.html', 'w', encoding='utf-8') as f:
        f.write(html)
```

### 3. A Través de SolverService (Recomendado)

```python
from app.services.solver_service import SolverService

solver_service = SolverService()

# Determinar métodos aplicables
suggested, not_applicable = solver_service.determine_applicable_methods(model)

# Resolver con el método específico
result = solver_service.solve(model, method="dual_simplex")

# La visualización HTML está incluida automáticamente
html_viz = result.get('html_visualization')
```

### 4. Desde API (Django Endpoint)

```python
import requests
import json

url = "http://localhost:8000/api/v1/analyze/solve"

payload = {
    "model": {
        "objective_function": "2*x1 + 3*x2",
        "objective": "min",
        "constraints": [
            "x1 + x2 >= 4",
            "2*x1 + x2 >= 5",
            "x1 >= 0",
            "x2 >= 0"
        ],
        "variables": {
            "x1": "Variable 1",
            "x2": "Variable 2"
        }
    },
    "method": "dual_simplex"
}

response = requests.post(url, json=payload)
result = response.json()
```

---

## 🧮 Algoritmo y Lógica

### Pasos del Algoritmo

#### 1. **Construcción del Tableau Inicial**

Para un problema:
```
Minimizar: z = 2x₁ + 3x₂
Sujeto a:
    x₁ + x₂ ≥ 4
    2x₁ + x₂ ≥ 5
    x₁, x₂ ≥ 0
```

Se transforma en:
```
Minimizar: z = 2x₁ + 3x₂
Sujeto a:
    -x₁ - x₂ + s₁ = -4    (multiplicar por -1)
    -2x₁ - x₂ + s₂ = -5   (multiplicar por -1)
    x₁, x₂, s₁, s₂ ≥ 0
```

**Tableau Inicial:**
```
Base | x₁  x₂  s₁  s₂ | RHS
-----|----------------|-----
 s₁  | -1  -1   1   0 | -4   ← RHS negativo (primal-infactible)
 s₂  | -2  -1   0   1 | -5   ← RHS negativo
-----|----------------|-----
  Z  |  2   3   0   0 |  0   ← Coeficientes positivos (dual-factible)
```

#### 2. **Selección de Fila Pivote (Variable Saliente)**

- Buscar la fila con el **RHS más negativo**
- Esta fila debe salir de la base para alcanzar factibilidad

En el ejemplo: Fila 2 (s₂) con RHS = -5

#### 3. **Selección de Columna Pivote (Variable Entrante)**

- Solo considerar columnas con **coeficientes negativos** en la fila pivote
- Calcular razón dual: `|c_j / a_{ij}|`
- Seleccionar la columna con **razón mínima**

**Cálculo de razones:**
```
Columna x₁: |2 / -2| = 1.0
Columna x₂: |3 / -1| = 3.0

Mínima → x₁ (columna 0)
```

#### 4. **Operaciones de Pivoteo**

- Dividir fila pivote por el elemento pivote
- Hacer ceros en el resto de la columna pivote
- Actualizar la base: `s₂ → x₁`

#### 5. **Verificar Factibilidad**

- Si todos los RHS ≥ 0 → **ÓPTIMO**
- Si no, repetir desde el paso 2

#### 6. **Criterios de Parada**

- ✅ **Óptimo**: Todos RHS ≥ 0 (primal-factible)
- ❌ **Infactible**: No hay columna con coeficiente negativo en fila pivote
- ⚠️ **Ciclado**: Máximo de iteraciones alcanzado

---

## 🎨 Visualización Gráfica

### Componentes de la Visualización HTML

#### 1. **Leyenda de Colores**
```
🔴 Elemento Pivote    - Celda destacada con borde grueso
🌸 Fila Pivote       - Fondo rosa claro
💙 Columna Pivote    - Fondo azul claro
🟠 RHS Negativo      - Fondo naranja (infactible)
💜 Variable Holgura  - Fondo púrpura claro
```

#### 2. **Caja de Variables de Holgura** (Iteración 0)
```
📊 Variables de Holgura Agregadas
• s₁ - Variable de holgura
• s₂ - Variable de holgura

Explicación: El método Simplex Dual comienza dual-factible
             (coeficientes de Z ≥ 0) pero puede ser
             primal-infactible (algunos RHS negativos)
```

#### 3. **Explicación del Paso**
```
📝 Explicación del Paso
Fila 1 tiene RHS más negativo. Columna 0 tiene razón dual mínima.

✅ Variable Entrante: x₁
❌ Variable Saliente: s₂
🎯 Elemento Pivote: -2.0000
📍 RHS de fila pivote (antes): -5.0000 (NEGATIVO)
```

#### 4. **Tabla de Razones Duales**
```
📊 Cálculo de Razones Duales
Razón = |Coeficiente Z / Coeficiente Fila Pivote|

Columna | Coef. Z | Coef. Fila Pivote | Razón  | ¿Mínima?
--------|---------|-------------------|--------|----------
   0    |  2.0000 |     -2.0000       | 1.0000 | ✓ SÍ
   1    |  3.0000 |     -1.0000       | 3.0000 | No
```

#### 5. **Tableau con Colores**
```html
<table class="tableau-table">
  <!-- Elemento pivote con fondo rojo -->
  <td class="pivot-cell">-2.0000</td>
  
  <!-- Celdas de fila pivote con fondo rosa -->
  <td class="pivot-row">-1.0000</td>
  
  <!-- RHS negativo con fondo naranja -->
  <td class="negative-rhs">-5.0000</td>
</table>
```

#### 6. **Indicador de Estado**
```
✅ SOLUCIÓN ÓPTIMA ALCANZADA
   Todos los RHS son no-negativos
```

### Ejemplo de HTML Generado

El sistema genera archivos HTML completamente autónomos con:
- CSS embebido para estilos
- Responsive design
- Tablas interactivas (hover effects)
- Márgenes y espaciado profesionales

---

## 📚 Ejemplos

### Ejemplo 1: Problema Básico

**Problema:**
```
Minimizar: z = 2x₁ + 3x₂
Sujeto a:
    x₁ + x₂ ≥ 4
    2x₁ + x₂ ≥ 5
    x₁, x₂ ≥ 0
```

**Solución:**
```
Valor óptimo: z = 8.0
x₁ = 4.0
x₂ = 0.0
Iteraciones: 3
```

**Archivo generado:** `dual_simplex_test1.html`

---

### Ejemplo 2: Problema con 3 Variables

**Problema:**
```
Minimizar: z = 3x₁ + 2x₂ + 4x₃
Sujeto a:
    x₁ + x₂ + x₃ ≥ 5
    2x₁ + x₂ ≥ 4
    x₁ + 3x₂ ≥ 6
    x₁, x₂, x₃ ≥ 0
```

**Solución:**
```
Valor óptimo: z = 10.0
x₁ = 0.0
x₂ = 5.0
x₃ = 0.0
Iteraciones: 3
```

**Archivo generado:** `dual_simplex_test2.html`

---

### Ejemplo 3: Problema Infactible

**Problema:**
```
Minimizar: z = x₁ + x₂
Sujeto a:
    x₁ + x₂ ≥ 5    ← Incompatible con la siguiente
    x₁ + x₂ ≤ 3    ← Ningún punto satisface ambas
    x₁, x₂ ≥ 0
```

**Resultado:**
```
Estado: infeasible
Error: El problema es infactible (no existe región factible)
Iteraciones: 2
```

**Archivo generado:** `dual_simplex_test3_infeasible.html`

---

## 🔧 Configuración y Extensión

### Personalizar Colores

Editar `dual_simplex_visualizer.py`:

```python
COLORS = {
    "pivot_cell": "#ff4444",      # Rojo para elemento pivote
    "pivot_row": "#ffcccc",       # Rosa claro para fila pivote
    "pivot_col": "#ccccff",       # Azul claro para columna pivote
    # ... más colores
}
```

### Ajustar Tolerancias

En `dual_simplex_method.py`:

```python
_TOL = 1e-10           # Tolerancia para comparaciones numéricas
_FEASIBLE_TOL = 1e-6   # Tolerancia para factibilidad
```

### Agregar Nuevos Formatos de Salida

Extender `DualSimplexVisualizer` con nuevos métodos:

```python
def generate_pdf_visualization(self, steps):
    # Implementar generación de PDF
    pass

def generate_json_summary(self, steps):
    # Implementar resumen JSON compacto
    pass
```

---

## 📊 Estructura de Datos

### Formato de `result`

```python
{
    "success": True,
    "method": "dual_simplex",
    "status": "optimal",  # o "infeasible"
    "objective_value": 8.0,
    "variables": {
        "x1": 4.0,
        "x2": 0.0
    },
    "iterations": 3,
    "equations_latex": "\\[x_1 + x_2 \\geq 4\\]\\n...",
    "steps": [
        {
            "iteration": 0,
            "type": "initial",
            "description": "Tableau inicial",
            "tableau_after": [[...]],
            "column_headers": ["x1", "x2", "s1", "s2", "RHS"],
            "row_labels": ["s1", "s2", "Z"],
            "is_feasible": False,
            # ...
        },
        {
            "iteration": 1,
            "type": "iteration",
            "entering_variable": "x1",
            "leaving_variable": "s2",
            "pivot_row": 1,
            "pivot_column": 0,
            "pivot_element": -2.0,
            "dual_ratios": [...],
            # ...
        }
    ],
    "html_visualization": "<html>...</html>"
}
```

---

## 🧪 Testing

### Ejecutar Pruebas

```powershell
cd backend
python test_dual_simplex.py
```

### Casos de Prueba Incluidos

1. ✅ Problema básico (2 variables, 2 restricciones)
2. ✅ Problema complejo (3 variables, 3 restricciones)
3. ✅ Problema infactible
4. ✅ Integración con SolverService

---

## 📖 Referencias

### Bibliografía

1. **Taha, H.A.** - "Operations Research: An Introduction" (Capítulo sobre Simplex Dual)
2. **Hillier & Lieberman** - "Introduction to Operations Research" (Dual Simplex Method)
3. **Winston, W.L.** - "Operations Research: Applications and Algorithms"

### Recursos Online

- [Wikipedia - Dual Simplex Algorithm](https://en.wikipedia.org/wiki/Dual_simplex_algorithm)
- MIT OpenCourseWare - Linear Programming Lectures

---

## 🤝 Contribuciones

Para agregar mejoras al método Simplex Dual:

1. Extender `DualSimplexMethod` con nuevas funcionalidades
2. Agregar tests en `test_dual_simplex.py`
3. Actualizar visualizaciones en `DualSimplexVisualizer`
4. Documentar cambios en este README

---

## 📝 Licencia

Este código forma parte de la Suite de Optimización Lineal y sigue la misma licencia del proyecto principal.

---

**Última actualización:** Noviembre 2025  
**Versión:** 1.0.0  
**Autor:** Suite de Optimización Lineal Team

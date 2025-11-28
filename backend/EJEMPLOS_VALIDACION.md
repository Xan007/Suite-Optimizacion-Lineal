# 🎬 Demostración Visual: Validación de Métodos en Acción

Este documento muestra ejemplos visuales de cómo funciona la validación implementada.

---

## 🧪 Ejemplo 1: Minimización + Simplex Normal (RECHAZADO)

### Entrada

```json
POST /api/v1/analyze/solve
Content-Type: application/json

{
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
      "x1": "Cantidad de producto A",
      "x2": "Cantidad de producto B"
    }
  },
  "method": "simplex"  ← ❌ MÉTODO NO PERMITIDO
}
```

### Salida (HTTP 400 Bad Request)

```json
{
  "success": false,
  "detail": "Los problemas de minimización solo pueden resolverse con el Método Simplex Dual o el Método de la Gran M. El método 'simplex' no está disponible para minimización.",
  "allowed_methods": [
    "dual_simplex",
    "big_m"
  ],
  "objective_type": "min"
}
```

### En la consola del servidor

```
ERROR 2025-11-27 - webapp.views - Método no permitido: simplex para problema de minimización
```

---

## ✅ Ejemplo 2: Minimización + Simplex Dual (ACEPTADO)

### Entrada

```json
POST /api/v1/analyze/solve
Content-Type: application/json

{
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
      "x1": "Cantidad de producto A",
      "x2": "Cantidad de producto B"
    }
  },
  "method": "dual_simplex"  ← ✅ MÉTODO PERMITIDO
}
```

### Salida (HTTP 200 OK)

```json
{
  "success": true,
  "result": {
    "success": true,
    "method": "dual_simplex",
    "status": "optimal",
    "objective_value": 8.0,
    "variables": {
      "x1": 4.0,
      "x2": 0.0
    },
    "iterations": 1,
    "steps": [
      {
        "iteration": 1,
        "type": "iteration",
        "description": "Iteración 1: Variable x1 sale de la base",
        "pivot_row": 0,
        "pivot_column": 0,
        "pivot_element": 2.0,
        "tableau_before": [...],
        "tableau_after": [...]
      }
    ],
    "html_visualization": "<div class='dual-simplex-solution'>...</div>",
    "explanation": "Método Simplex Dual: 1 iteración hasta optimalidad"
  }
}
```

---

## 🧪 Ejemplo 3: Minimización + Método Gráfico (RECHAZADO)

### Entrada

```json
POST /api/v1/analyze/solve
Content-Type: application/json

{
  "model": {
    "objective_function": "5*x + 3*y",
    "objective": "min",
    "constraints": [
      "2*x + y >= 6",
      "x + 2*y >= 4",
      "x >= 0",
      "y >= 0"
    ],
    "variables": {
      "x": "Variable X",
      "y": "Variable Y"
    }
  },
  "method": "graphical"  ← ❌ MÉTODO NO PERMITIDO
}
```

### Salida (HTTP 400 Bad Request)

```json
{
  "success": false,
  "detail": "Los problemas de minimización solo pueden resolverse con el Método Simplex Dual o el Método de la Gran M. El método 'graphical' no está disponible para minimización.",
  "allowed_methods": [
    "dual_simplex",
    "big_m"
  ],
  "objective_type": "min"
}
```

---

## ✅ Ejemplo 4: Maximización + Todos los Métodos (ACEPTADOS)

### 4.1 Maximización + Simplex Normal ✅

```json
{
  "model": {
    "objective_function": "3*x1 + 2*x2",
    "objective": "max",
    "constraints": ["2*x1 + x2 <= 10", "x1 >= 0", "x2 >= 0"],
    "variables": {"x1": "Var 1", "x2": "Var 2"}
  },
  "method": "simplex"
}
```

**Resultado**: HTTP 200 ✅
```json
{
  "success": true,
  "result": {
    "success": true,
    "method": "simplex",
    "status": "optimal",
    "objective_value": 15.0,
    "variables": {"x1": 5.0, "x2": 0.0},
    "iterations": 1
  }
}
```

---

### 4.2 Maximización + Método Gráfico ✅

```json
{
  "model": {
    "objective_function": "3*x1 + 2*x2",
    "objective": "max",
    "constraints": ["2*x1 + x2 <= 10", "x1 + 2*x2 <= 8", "x1 >= 0", "x2 >= 0"],
    "variables": {"x1": "Var 1", "x2": "Var 2"}
  },
  "method": "graphical"
}
```

**Resultado**: HTTP 200 ✅
```json
{
  "success": true,
  "result": {
    "success": true,
    "method": "graphical",
    "status": "optimal",
    "objective_value": 16.0,
    "optimal_point": [4.0, 2.0],
    "feasible_points": [
      {"point": [0, 0], "objective": 0, "is_optimal": false},
      {"point": [5, 0], "objective": 15, "is_optimal": false},
      {"point": [4, 2], "objective": 16, "is_optimal": true},
      {"point": [0, 4], "objective": 8, "is_optimal": false}
    ],
    "graph": {
      "image": "data:image/png;base64,iVBORw0KG...",
      "vertices_table": [...],
      "solution_block": {...}
    }
  }
}
```

---

## 📊 Tabla Resumen de Validación

| Objetivo | Método | HTTP Status | Success | Mensaje |
|----------|--------|-------------|---------|---------|
| `min` | `simplex` | 400 | false | "Los problemas de minimización solo pueden..." |
| `min` | `graphical` | 400 | false | "Los problemas de minimización solo pueden..." |
| `min` | `dual_simplex` | 200 | true | Solución óptima |
| `min` | `big_m` | 200 | true | Solución óptima |
| `max` | `simplex` | 200 | true | Solución óptima |
| `max` | `graphical` | 200 | true | Solución óptima |
| `max` | `dual_simplex` | 200 | true | Solución óptima |
| `max` | `big_m` | 200 | true | Solución óptima |

---

## 🔍 Flujo Completo de Validación

### Caso: Usuario intenta resolver minimización con Simplex

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Cliente envía petición                                   │
│    POST /api/v1/analyze/solve                               │
│    {model: {..., objective: "min"}, method: "simplex"}      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Endpoint: webapp/views.py → solve_model()               │
│    • Parsea JSON                                            │
│    • Crea MathematicalModel                                 │
│    • Detecta: model.objective == "min"                      │
│    • Detecta: method == "simplex"                           │
│    • ❌ VALIDACIÓN FALLA                                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Retorna HTTP 400 Bad Request                             │
│    {                                                         │
│      "success": false,                                      │
│      "detail": "Los problemas de minimización...",          │
│      "allowed_methods": ["dual_simplex", "big_m"],          │
│      "objective_type": "min"                                │
│    }                                                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Cliente recibe error                                     │
│    • Muestra mensaje al usuario                             │
│    • Sugiere usar: dual_simplex o big_m                     │
│    • Deshabilita botón "Simplex" para minimización          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Uso desde el Frontend

### JavaScript/TypeScript Example

```typescript
// Función para resolver problema
async function solveProblem(model: MathematicalModel, method: string) {
  try {
    const response = await fetch('/api/v1/analyze/solve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, method })
    });
    
    if (response.status === 400) {
      // ❌ Método no permitido
      const error = await response.json();
      
      // Mostrar mensaje de error
      showErrorMessage(error.detail);
      
      // Mostrar métodos permitidos
      showAllowedMethods(error.allowed_methods);
      
      console.error(`Error: ${error.detail}`);
      console.info(`Métodos permitidos: ${error.allowed_methods.join(', ')}`);
      
      return null;
    }
    
    if (response.ok) {
      // ✅ Solución obtenida
      const data = await response.json();
      return data.result;
    }
    
  } catch (error) {
    console.error('Error de red:', error);
  }
}

// Función para obtener métodos disponibles después del análisis
async function getAvailableMethods(model: MathematicalModel) {
  const response = await fetch('/api/v1/analyze/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ problem: model.context })
  });
  
  const data = await response.json();
  
  // Deshabilitar métodos no aplicables
  const notApplicable = data.methods_not_applicable || {};
  
  for (const [method, reason] of Object.entries(notApplicable)) {
    disableMethodButton(method, reason);
  }
  
  // Destacar métodos sugeridos
  const suggested = data.suggested_methods || [];
  for (const method of suggested) {
    highlightMethodButton(method);
  }
}
```

---

## 🖼️ UI/UX Sugerido

### Estado de Botones para Minimización

```
┌────────────────────────────────────────────────────────────┐
│ Métodos de Solución                                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [ Simplex Normal ]  ← DESHABILITADO                      │
│  ⚠️ No disponible para problemas de minimización          │
│                                                            │
│  [ Método Gráfico ]  ← DESHABILITADO                      │
│  ⚠️ No disponible para problemas de minimización          │
│                                                            │
│  [ ✨ Simplex Dual ]  ← DESTACADO/RECOMENDADO            │
│  💡 Método óptimo para este problema                      │
│                                                            │
│  [ Gran M ]  ← DISPONIBLE                                 │
│  💡 Método universal                                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Estado de Botones para Maximización

```
┌────────────────────────────────────────────────────────────┐
│ Métodos de Solución                                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [ ✨ Simplex Normal ]  ← DESTACADO/RECOMENDADO           │
│  💡 Método estándar para maximización                     │
│                                                            │
│  [ Método Gráfico ]  ← DISPONIBLE (si ≤ 2 variables)     │
│  📊 Visualización gráfica                                 │
│                                                            │
│  [ Simplex Dual ]  ← DISPONIBLE                           │
│  🔄 Método alternativo                                     │
│                                                            │
│  [ Gran M ]  ← DISPONIBLE                                 │
│  💡 Método universal                                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📱 Mensaje de Error Mejorado (Ejemplo UI)

```
┌────────────────────────────────────────────────────────────┐
│ ⚠️ Método No Disponible                                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Los problemas de minimización solo pueden resolverse      │
│ con el Método Simplex Dual o el Método de la Gran M.      │
│                                                            │
│ El método 'Simplex Normal' no está disponible para        │
│ minimización.                                              │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 💡 Métodos Recomendados:                               │ │
│ │                                                        │ │
│ │  • Simplex Dual - Método óptimo para minimización     │ │
│ │    con restricciones >=                               │ │
│ │                                                        │ │
│ │  • Gran M - Método universal que maneja cualquier     │ │
│ │    combinación de restricciones                       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│  [ Usar Simplex Dual ]  [ Usar Gran M ]  [ Cancelar ]     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🎓 Mensaje Educativo (Opcional)

```
┌────────────────────────────────────────────────────────────┐
│ 📚 ¿Por qué este método no está disponible?               │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ El Método Simplex Normal está diseñado específicamente    │
│ para problemas de maximización con restricciones <=.      │
│                                                            │
│ Para problemas de minimización con restricciones >=,      │
│ el Método Simplex Dual es más eficiente y teóricamente    │
│ correcto.                                                  │
│                                                            │
│  [ Más información ]  [ Entendido ]                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

**Este documento proporciona ejemplos visuales completos de cómo se comporta la validación implementada.**

Fecha: 27 de Noviembre, 2025

# 🌐 Guía de Uso: API y Frontend

## Cómo Usar el Método Simplex Dual desde la API

---

## 🚀 Quick Start

### 1. Iniciar el Servidor Django

```powershell
cd backend
python manage.py runserver
```

El servidor estará disponible en: `http://localhost:8000`

---

## 📡 Endpoints Disponibles

### 1. Resolver Problema (Método Simplex Dual)

**Endpoint:** `POST /api/v1/analyze/solve`

**Request Body:**
```json
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
      "x1": "Variable de decisión 1",
      "x2": "Variable de decisión 2"
    },
    "context": "Problema de minimización con restricciones >="
  },
  "method": "dual_simplex"
}
```

**Response:**
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
    "iterations": 3,
    "equations_latex": "\\[x_1 + x_2 \\geq 4\\]\\n\\[2x_1 + x_2 \\geq 5\\]",
    "steps": [
      {
        "iteration": 0,
        "type": "initial",
        "description": "Tableau inicial - Método Simplex Dual",
        "tableau_after": [[...]], 
        "column_headers": ["x1", "x2", "s1", "s2", "RHS"],
        "row_labels": ["s1", "s2", "Z (Función Objetivo)"],
        "is_feasible": false,
        "reasoning": {...}
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
        "tableau_before": [[...]],
        "tableau_after": [[...]],
        "is_feasible": false
      },
      ...
    ],
    "html_visualization": "<html>...</html>"
  }
}
```

---

## 💻 Ejemplos de Uso

### Ejemplo 1: cURL (Linux/Mac/PowerShell)

```bash
curl -X POST http://localhost:8000/api/v1/analyze/solve \
  -H "Content-Type: application/json" \
  -d '{
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
        "x1": "Cantidad de producto 1",
        "x2": "Cantidad de producto 2"
      }
    },
    "method": "dual_simplex"
  }'
```

### Ejemplo 2: Python (requests)

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

print(f"Éxito: {result['success']}")
print(f"Valor óptimo: {result['result']['objective_value']}")
print(f"Solución: {result['result']['variables']}")

# Guardar visualización HTML
if 'html_visualization' in result['result']:
    with open('resultado.html', 'w', encoding='utf-8') as f:
        f.write(result['result']['html_visualization'])
    print("✅ Visualización guardada en resultado.html")
```

### Ejemplo 3: JavaScript (Fetch API)

```javascript
const url = 'http://localhost:8000/api/v1/analyze/solve';

const payload = {
  model: {
    objective_function: "2*x1 + 3*x2",
    objective: "min",
    constraints: [
      "x1 + x2 >= 4",
      "2*x1 + x2 >= 5",
      "x1 >= 0",
      "x2 >= 0"
    ],
    variables: {
      x1: "Variable 1",
      x2: "Variable 2"
    }
  },
  method: "dual_simplex"
};

fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payload)
})
.then(response => response.json())
.then(data => {
  console.log('Éxito:', data.success);
  console.log('Valor óptimo:', data.result.objective_value);
  console.log('Solución:', data.result.variables);
  
  // Mostrar visualización HTML en iframe
  if (data.result.html_visualization) {
    const iframe = document.createElement('iframe');
    iframe.srcdoc = data.result.html_visualization;
    iframe.style.width = '100%';
    iframe.style.height = '800px';
    document.body.appendChild(iframe);
  }
})
.catch(error => console.error('Error:', error));
```

### Ejemplo 4: PowerShell

```powershell
$url = "http://localhost:8000/api/v1/analyze/solve"

$payload = @{
    model = @{
        objective_function = "2*x1 + 3*x2"
        objective = "min"
        constraints = @(
            "x1 + x2 >= 4",
            "2*x1 + x2 >= 5",
            "x1 >= 0",
            "x2 >= 0"
        )
        variables = @{
            x1 = "Variable 1"
            x2 = "Variable 2"
        }
    }
    method = "dual_simplex"
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri $url -Method Post -Body $payload -ContentType "application/json"

Write-Host "Éxito: $($response.success)"
Write-Host "Valor óptimo: $($response.result.objective_value)"
Write-Host "Solución: $($response.result.variables | ConvertTo-Json)"

# Guardar HTML
if ($response.result.html_visualization) {
    $response.result.html_visualization | Out-File -FilePath "resultado.html" -Encoding UTF8
    Write-Host "✅ Visualización guardada en resultado.html"
}
```

---

## 🎯 Métodos Disponibles

El endpoint acepta los siguientes métodos en el parámetro `method`:

| Método | Descripción | Cuándo Usar |
|--------|-------------|-------------|
| `"dual_simplex"` | **Simplex Dual** | Minimización con ≥ |
| `"simplex"` | Simplex Primal | Maximización con ≤ |
| `"big_m"` | Gran M | Restricciones =, ≥ |
| `"graphical"` | Método Gráfico | 2 variables |

---

## 🔍 Detección Automática de Métodos

También puedes omitir el parámetro `method` y el sistema detectará automáticamente el mejor método:

```json
{
  "model": {
    "objective_function": "2*x1 + 3*x2",
    "objective": "min",
    "constraints": ["x1 + x2 >= 4", "2*x1 + x2 >= 5"],
    "variables": {"x1": "Var 1", "x2": "Var 2"}
  }
}
```

El sistema aplicará automáticamente `dual_simplex` porque detecta:
- ✅ Objetivo: minimización
- ✅ Restricciones: >=

---

## 📊 Procesamiento de la Respuesta

### Acceder a los Pasos (Steps)

```python
steps = result['result']['steps']

for step in steps:
    print(f"\n--- Iteración {step['iteration']} ---")
    print(f"Descripción: {step['description']}")
    
    if step['type'] == 'iteration':
        print(f"  Entra: {step['entering_variable']}")
        print(f"  Sale: {step['leaving_variable']}")
        print(f"  Pivote: fila {step['pivot_row']}, col {step['pivot_column']}")
        print(f"  Elemento: {step['pivot_element']}")
        
        # Tableau después del pivoteo
        tableau = step['tableau_after']
        headers = step['column_headers']
        
        print("\n  Tableau:")
        print("  " + " | ".join(headers))
        for row in tableau:
            print("  " + " | ".join([f"{v:7.3f}" for v in row]))
```

### Renderizar Visualización HTML

**Opción 1: Guardar como archivo**
```python
with open('resultado.html', 'w', encoding='utf-8') as f:
    f.write(result['result']['html_visualization'])
```

**Opción 2: Mostrar en navegador (Python)**
```python
import webbrowser
import tempfile

with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
    f.write(result['result']['html_visualization'])
    webbrowser.open(f.name)
```

**Opción 3: Enviar al frontend**
```javascript
// En el frontend (React, Vue, etc.)
<iframe 
  srcDoc={result.result.html_visualization}
  style={{width: '100%', height: '800px', border: 'none'}}
/>
```

---

## 🧪 Testing del API

### Test con Python unittest

```python
import unittest
import requests

class TestDualSimplexAPI(unittest.TestCase):
    def setUp(self):
        self.url = "http://localhost:8000/api/v1/analyze/solve"
    
    def test_basic_problem(self):
        payload = {
            "model": {
                "objective_function": "2*x1 + 3*x2",
                "objective": "min",
                "constraints": [
                    "x1 + x2 >= 4",
                    "2*x1 + x2 >= 5",
                    "x1 >= 0", "x2 >= 0"
                ],
                "variables": {"x1": "Var 1", "x2": "Var 2"}
            },
            "method": "dual_simplex"
        }
        
        response = requests.post(self.url, json=payload)
        result = response.json()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['result']['status'], 'optimal')
        self.assertAlmostEqual(result['result']['objective_value'], 8.0)
        self.assertAlmostEqual(result['result']['variables']['x1'], 4.0)
        self.assertAlmostEqual(result['result']['variables']['x2'], 0.0)
    
    def test_infeasible_problem(self):
        payload = {
            "model": {
                "objective_function": "x1 + x2",
                "objective": "min",
                "constraints": [
                    "x1 + x2 >= 5",
                    "x1 + x2 <= 3",
                    "x1 >= 0", "x2 >= 0"
                ],
                "variables": {"x1": "Var 1", "x2": "Var 2"}
            },
            "method": "dual_simplex"
        }
        
        response = requests.post(self.url, json=payload)
        result = response.json()
        
        self.assertFalse(result['result']['success'])
        self.assertEqual(result['result']['status'], 'infeasible')

if __name__ == '__main__':
    unittest.main()
```

---

## 🔐 Autenticación (Futuro)

Actualmente el API no requiere autenticación, pero si se implementa:

```python
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_API_TOKEN'
}

response = requests.post(url, json=payload, headers=headers)
```

---

## ⚠️ Manejo de Errores

### Errores Comunes

**1. Problema no lineal:**
```json
{
  "success": false,
  "error": "El problema no es lineal"
}
```

**2. Método no aplicable:**
```json
{
  "success": false,
  "error": "El método Simplex Dual solo se aplica a problemas de minimización"
}
```

**3. Problema infactible:**
```json
{
  "success": false,
  "status": "infeasible",
  "error": "El problema es infactible (no existe región factible)",
  "iterations": 2,
  "steps": [...]
}
```

**4. Formato JSON inválido:**
```json
{
  "detail": "JSON inválido: ..."
}
```

### Ejemplo de Manejo de Errores en Python

```python
try:
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    
    if not result.get('success'):
        print(f"❌ Error: {result.get('error', 'Error desconocido')}")
        return
    
    if not result['result'].get('success'):
        print(f"❌ Problema: {result['result'].get('error', 'No se pudo resolver')}")
        print(f"Estado: {result['result'].get('status')}")
        return
    
    # Procesar resultado exitoso
    print(f"✅ Valor óptimo: {result['result']['objective_value']}")
    
except requests.Timeout:
    print("⏱️ Timeout: El servidor tardó demasiado en responder")
except requests.ConnectionError:
    print("🔌 Error de conexión: No se pudo conectar al servidor")
except requests.HTTPError as e:
    print(f"❌ Error HTTP: {e}")
except Exception as e:
    print(f"❌ Error inesperado: {e}")
```

---

## 📈 Rate Limiting (Futuro)

Si se implementa rate limiting:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## 🌍 CORS

El servidor Django está configurado para permitir peticiones CORS desde cualquier origen (desarrollo).

Para producción, configurar en `optiline/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "https://tu-frontend.com",
    "https://www.tu-frontend.com",
]
```

---

## 📦 Integración con Frameworks Frontend

### React

```jsx
import React, { useState } from 'react';

function DualSimplexSolver() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const solve = async () => {
    setLoading(true);
    
    const payload = {
      model: {
        objective_function: "2*x1 + 3*x2",
        objective: "min",
        constraints: ["x1 + x2 >= 4", "2*x1 + x2 >= 5", "x1 >= 0", "x2 >= 0"],
        variables: { x1: "Var 1", x2: "Var 2" }
      },
      method: "dual_simplex"
    };
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/analyze/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      const data = await response.json();
      setResult(data.result);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <button onClick={solve} disabled={loading}>
        {loading ? 'Resolviendo...' : 'Resolver con Simplex Dual'}
      </button>
      
      {result && (
        <div>
          <h3>Resultado:</h3>
          <p>Valor óptimo: {result.objective_value}</p>
          <p>x1 = {result.variables.x1}</p>
          <p>x2 = {result.variables.x2}</p>
          
          <iframe 
            srcDoc={result.html_visualization}
            style={{width: '100%', height: '800px', border: 'none'}}
          />
        </div>
      )}
    </div>
  );
}

export default DualSimplexSolver;
```

### Vue.js

```vue
<template>
  <div>
    <button @click="solve" :disabled="loading">
      {{ loading ? 'Resolviendo...' : 'Resolver con Simplex Dual' }}
    </button>
    
    <div v-if="result">
      <h3>Resultado:</h3>
      <p>Valor óptimo: {{ result.objective_value }}</p>
      <p>x1 = {{ result.variables.x1 }}</p>
      <p>x2 = {{ result.variables.x2 }}</p>
      
      <iframe 
        :srcdoc="result.html_visualization"
        style="width: 100%; height: 800px; border: none"
      />
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      result: null,
      loading: false
    };
  },
  methods: {
    async solve() {
      this.loading = true;
      
      const payload = {
        model: {
          objective_function: "2*x1 + 3*x2",
          objective: "min",
          constraints: ["x1 + x2 >= 4", "2*x1 + x2 >= 5", "x1 >= 0", "x2 >= 0"],
          variables: { x1: "Var 1", x2: "Var 2" }
        },
        method: "dual_simplex"
      };
      
      try {
        const response = await fetch('http://localhost:8000/api/v1/analyze/solve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        this.result = data.result;
      } catch (error) {
        console.error('Error:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

---

## 📝 Resumen de Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/test/` | GET | Health check |
| `/api/v1/analyze/` | POST | Analizar problema de texto |
| `/api/v1/analyze/solve` | POST | **Resolver con método específico** |
| `/api/v1/analyze/validate-model` | POST | Validar modelo matemático |
| `/api/v1/analyze/get-representations` | POST | Obtener representaciones |
| `/api/v1/analyze/analyze-image` | POST | Analizar desde imagen |

---

**¡El API está completo y listo para usar! 🎉**

Ejecuta `python manage.py runserver` y empieza a resolver problemas de optimización con Simplex Dual.

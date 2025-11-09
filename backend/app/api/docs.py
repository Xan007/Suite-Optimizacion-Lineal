"""
Documentación centralizada de los endpoints del API.
Este módulo contiene las docstrings y ejemplos para todos los endpoints,
separado de la lógica de las rutas para mantener el código limpio.
"""

# ============================================================================
# ENDPOINT: POST /analyze/ - Análisis Completo
# ============================================================================

ANALYZE_ENDPOINT_DOC = """
**Análisis Completo - De Texto a Todas las Representaciones**

Realiza un análisis completo de un problema de optimización lineal:
1. Envías el problema en texto natural
2. Groq extrae automáticamente el modelo matemático
3. SymPy normaliza y valida el problema
4. Se generan automáticamente 5 representaciones matemáticas

**Representaciones generadas:**
- **Canónica:** Forma original del problema
- **Estándar:** Normalizada para algoritmos (ej: simplex)
- **Matricial:** Formato Ax=b con matrices en JSON arrays
- **Dual:** Problema dual derivado del primal
- **Big M:** Método de la Gran M para restricciones >= o =

**Ejemplo de entrada:**
```json
{
  "problem": "Una fábrica produce dos productos A y B. Producto A requiere 2 horas y genera $3 de ganancia. Producto B requiere 1 hora y genera $2 de ganancia. Se tienen 10 horas disponibles. ¿Cuántos productos de cada uno deben producir para maximizar la ganancia?",
  "groq_model": "openai/gpt-oss-20b"
}
```

**Campos del request:**
- `problem` (requerido): Descripción del problema en lenguaje natural
- `api_key` (opcional): Tu API key de Groq. Si no incluyes, usa la del .env
- `groq_model` (opcional): Modelo de Groq. Defecto: configurado en .env

**Respuesta incluye:**
- `raw_analysis`: Análisis textual de Groq
- `mathematical_model`: Modelo extraído (forma canónica)
- `representations`: Diccionario con las 4 formas (canonical, standard, matrix, dual)
- `is_linear`: true si es problema lineal

**Códigos de respuesta:**
- 200: Análisis exitoso
- 400: Problema no es lineal o formato inválido
- 401: API key faltante
- 500: Error interno del servidor
"""

# ============================================================================
# ENDPOINT: POST /analyze/validate-model - Validar Modelo
# ============================================================================

VALIDATE_MODEL_ENDPOINT_DOC = """
**Validar Modelo Matemático con SymPy**

Valida que un modelo matemático sea correcto usando SymPy.

**Ejemplo de entrada:**
```json
{
  "objective_function": "3*x1 + 2*x2",
  "objective": "max",
  "constraints": ["2*x1 + x2 <= 10"],
  "variables": {
    "x1": "Cantidad producto A",
    "x2": "Cantidad producto B"
  },
  "context": "Problema de producción"
}
```

**Campos del request:**
- `objective_function` (requerido): Expresión matemática ej: "3*x1 + 2*x2"
- `objective` (requerido): "max" o "min"
- `constraints` (requerido): Lista de restricciones ej: ["2*x1 + x2 <= 10", "x1 >= 0"]
- `variables` (requerido): Diccionario con descripciones de variables
- `context` (opcional): Contexto del problema

**Respuesta:**
- `is_valid`: true si el modelo es válido
- `sympy_expressions`: Expresiones procesadas por SymPy
- `message`: Mensaje descriptivo

**Códigos de respuesta:**
- 200: Validación completada
- 400: Modelo inválido
- 500: Error interno del servidor
"""

# ============================================================================
# ENDPOINT: POST /analyze/get-representations - Generar Representaciones
# ============================================================================

GET_REPRESENTATIONS_ENDPOINT_DOC = """
**Generar Todas las Representaciones de un Modelo**

Genera 4 representaciones matemáticas (canónica, estándar, matricial, dual) 
a partir de un modelo ya procesado por SymPy.

**Cuándo usar:**
- Ya tienes un modelo procesado de otra fuente
- Quieres regenerar las representaciones
- Necesitas solo las representaciones sin análisis de Groq

**Ejemplo de entrada (formato simplificado):**
```json
{
  "objective": "max",
  "objective_function": "3*x1 + 2*x2",
  "constraints": [
    {
      "lhs": "2*x1 + x2",
      "operator": "<=",
      "rhs": 10.0
    }
  ],
  "variables": {
    "x1": "Cantidad A",
    "x2": "Cantidad B"
  }
}
```

**Campos requeridos:**
- `objective`: "max" o "min"
- `objective_function`: Expresión SymPy como string
- `constraints`: Lista de restricciones con estructura {lhs, operator, rhs}
- `variables`: Diccionario de variables

**Respuesta:**
```json
{
  "success": true,
  "representations": {
    "canonical": {...},
    "standard": {...},
    "matrix": {...},
    "dual": {...}
  }
}
```

**Códigos de respuesta:**
- 200: Representaciones generadas exitosamente
- 400: Modelo inválido
- 500: Error interno del servidor
"""

# ============================================================================
# ENDPOINT: POST /analyze/analyze-image - Análisis desde Imagen
# ============================================================================

ANALYZE_IMAGE_ENDPOINT_DOC = """
**Análisis desde Imagen - De Foto a Todas las Representaciones**

Analiza un problema de optimización lineal desde una imagen (foto, captura, PDF escaneado).
Groq vision extrae el texto de la imagen y realiza análisis completo.

**Cuándo usar:**
- Tienes el problema en foto/captura de pantalla
- Problema escrito en papel fotografiado
- Documento escaneado con problema de optimización

**Cómo usar (multipart/form-data):**
```
POST /analyze/analyze-image

Form data:
- file: [seleccionar archivo de imagen: PNG, JPG, etc.]
- problem_description: "Problema adicional escrito a mano" (opcional)
- api_key: "tu-groq-api-key" (opcional, usa .env si no incluyes)
- groq_model: "openai/gpt-oss-20b" (opcional)
```

**Formato de respuesta:**
Idéntico a `/analyze/`:
- raw_analysis: Análisis textual de Groq
- mathematical_model: Modelo extraído
- representations: 4 formas (canonical, standard, matrix, dual)
- is_linear: true si es lineal

**Tipos de archivo soportados:**
- Imágenes: PNG, JPG, JPEG, GIF, WebP
- Documentos: Cualquier formato de imagen (escaneados)

**Códigos de respuesta:**
- 200: Análisis exitoso
- 400: Archivo no es imagen válida o problema no es lineal
- 401: API key faltante
- 500: Error interno del servidor
"""

# ============================================================================
# EJEMPLOS Y ESQUEMAS DE RESPUESTA
# ============================================================================

MATHEMATICAL_MODEL_EXAMPLE = {
    "objective_function": "3*x1 + 2*x2",
    "objective": "max",
    "constraints": ["2*x1 + x2 <= 10"],
    "variables": {
        "x1": "Unidades de producto A a producir",
        "x2": "Unidades de producto B a producir"
    },
    "context": "Fábrica con 2 productos. Producto A: 2h de trabajo y $3 ganancia. Producto B: 1h de trabajo y $2 ganancia. Máximo 10 horas disponibles. Objetivo: maximizar ganancia total."
}

ANALYZE_RESPONSE_EXAMPLE = {
    "raw_analysis": "Este es un problema de programación lineal de maximización. Se trata de una situación de producción donde una fábrica necesita determinar la cantidad de dos productos a manufacturar para maximizar ganancias sujeto a restricciones de horas disponibles...",
    "mathematical_model": MATHEMATICAL_MODEL_EXAMPLE,
    "representations": {
        "canonical": {
            "form": "canonical",
            "objective": "max",
            "objective_function": "3*x1 + 2*x2",
            "constraints": [
                {"expression": "2*x1 + x2", "operator": "<=", "rhs": 10.0}
            ],
            "variables": {
                "x1": "Unidades de producto A",
                "x2": "Unidades de producto B"
            }
        },
        "standard": {
            "form": "standard",
            "objective": "max",
            "objective_function": "3*x1 + 2*x2",
            "constraints": [
                {"expression": "2*x1 + x2 + s1", "operator": "=", "rhs": 10.0}
            ],
            "slack_variables": {"s1": "Holgura 1"},
            "non_negativity": [
                {"expression": "x1", "operator": ">=", "rhs": 0},
                {"expression": "x2", "operator": ">=", "rhs": 0},
                {"expression": "s1", "operator": ">=", "rhs": 0}
            ]
        },
        "matrix": {
            "form": "matrix",
            "objective": "max",
            "A": [[2, 1]],
            "b": [[10]],
            "c": [[3, 2]],
            "variables": ["x1", "x2"],
            "dimensions": {"constraints": 1, "variables": 2},
            "note": "Non-negativity conditions (x >= 0) are implicit"
        },
        "dual": {
            "form": "dual",
            "objective": "min",
            "objective_function": "10.0*y1",
            "constraints": [
                {"expression": "2*y1", "operator": ">=", "rhs": 3.0},
                {"expression": "y1", "operator": ">=", "rhs": 2.0}
            ],
            "variables": {"y1": "Dual variable for constraint 1"},
            "primal_objective": "max",
            "primal_variables_count": 2,
            "dual_variables_count": 1
        }
    },
    "groq_model": "openai/gpt-oss-20b",
    "is_linear": True
}

VALIDATE_MODEL_RESPONSE_EXAMPLE = {
    "is_valid": True,
    "sympy_expressions": {
        "objective": "3*x1 + 2*x2",
        "constraints": ["2*x1 + x2 - 10"]
    },
    "message": "Modelo validado correctamente"
}

GET_REPRESENTATIONS_RESPONSE_EXAMPLE = {
    "success": True,
    "representations": {
        "canonical": {...},
        "standard": {...},
        "matrix": {...},
        "dual": {...},
        "big_m": {...}
    }
}

BIG_M_FORM_EXAMPLE = {
    "form": "big_m",
    "objective": "max",
    "objective_function": "3*x1 + 2*x2 - M*A1",
    "constraints": [
        {
            "expression": "2*x1 + x2 - s1 + A1",
            "operator": "=",
            "rhs": 10
        }
    ],
    "non_negativity": [
        {"expression": "x1", "operator": ">=", "rhs": 0},
        {"expression": "x2", "operator": ">=", "rhs": 0},
        {"expression": "s1", "operator": ">=", "rhs": 0},
        {"expression": "A1", "operator": ">=", "rhs": 0}
    ],
    "slack_variables": {"s1": "Holgura 1"},
    "artificial_variables": {"A1": "Variable artificial 1"},
    "M": "Constante grande usada para penalizar las variables artificiales (típicamente 10^6)",
    "description": "Método de la Gran M para problemas con restricciones >= o ="
}

# ============================================================================
# GUÍA DE USO Y FLUJOS DE TRABAJO
# ============================================================================

USAGE_GUIDE = """
# Guía de Uso de los Endpoints

## Flujo 1: Análisis Completo (Recomendado)
**Cuándo usar:** Tienes un problema en texto y quieres TODA la información

```bash
curl -X POST http://localhost:8000/analyze/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "problem": "Una fábrica produce dos productos...",
    "groq_model": "openai/gpt-oss-20b"
  }'
```

**Resultado:** Una sola respuesta con:
- ✅ Análisis textual de Groq
- ✅ Modelo matemático extraído
- ✅ 4 representaciones automáticas (canonical, standard, matrix, dual)

---

## Flujo 2: Análisis desde Imagen
**Cuándo usar:** El problema está en una foto, captura o documento escaneado

```bash
curl -X POST http://localhost:8000/analyze/analyze-image \\
  -F "file=@problema.jpg" \\
  -F "groq_model=openai/gpt-oss-20b"
```

**Resultado:** Idéntico a Flujo 1, pero el texto se extrae de la imagen

---

## Flujo 3: Validar Modelo Existente
**Cuándo usar:** Tienes un modelo y solo quieres validarlo

```bash
curl -X POST http://localhost:8000/analyze/validate-model \\
  -H "Content-Type: application/json" \\
  -d '{
    "objective_function": "3*x1 + 2*x2",
    "objective": "max",
    "constraints": ["2*x1 + x2 <= 10"],
    "variables": {"x1": "V1", "x2": "V2"}
  }'
```

**Resultado:**
- is_valid: true/false
- sympy_expressions: Expresiones procesadas
- message: Descripción del resultado

---

## Flujo 4: Regenerar Representaciones
**Cuándo usar:** Tienes un modelo procesado y solo quieres sus representaciones

```bash
curl -X POST http://localhost:8000/analyze/get-representations \\
  -H "Content-Type: application/json" \\
  -d '{
    "objective": "max",
    "objective_function": "3*x1 + 2*x2",
    "constraints": [...],
    "variables": {"x1": "V1", "x2": "V2"}
  }'
```

**Resultado:** Las 4 representaciones (canonical, standard, matrix, dual)

---

## Flujo 5: Método de la Gran M
**Cuándo usar:** Tu problema tiene restricciones >= o = (requiere variables artificiales)

El endpoint `/analyze/` automáticamente incluye la forma Big M en las representaciones.

**Características de Big M:**
- Agrega variables de holgura para restricciones <=
- Agrega variables de exceso para restricciones >=
- Agrega variables artificiales para restricciones >= o =
- Penaliza variables artificiales con -M en la función objetivo
- M es una constante suficientemente grande (típicamente 10^6)
- Las variables artificiales deben valer 0 en la solución óptima

**Ejemplo de respuesta (representación big_m):**
```json
{
  "form": "big_m",
  "objective": "max",
  "objective_function": "3*x1 + 2*x2 - M*A1",
  "constraints": [
    {
      "expression": "2*x1 + x2 - s1 + A1",
      "operator": "=",
      "rhs": 10
    }
  ],
  "non_negativity": [
    {"expression": "x1", "operator": ">=", "rhs": 0},
    {"expression": "x2", "operator": ">=", "rhs": 0},
    {"expression": "s1", "operator": ">=", "rhs": 0},
    {"expression": "A1", "operator": ">=", "rhs": 0}
  ],
  "slack_variables": {"s1": "Holgura 1"},
  "artificial_variables": {"A1": "Variable artificial 1"},
  "M": "Constante grande (típicamente 10^6)"
}
```

---

## Características Implementadas

✅ **Modelos Centralizados:** Todos usan settings.GROQ_MODEL
✅ **Matrices como JSON:** [[2, 1]] no "Matrix([[2, 1]])"
✅ **Términos Reordenados:** 2*x1 + x2 + s1 (variables originales, luego holguras)
✅ **Expresiones Limpias:** 4*x1 no 4*x*1
✅ **Respeta Objetivo Original:** No força max/min
✅ **No-negatividad Correcta:** Filtrada de matriz, incluida en estándar
✅ **Dual Correcto:** Restricciones reales, no "0 >= 0"
✅ **Big M:** Variables artificiales penalizadas correctamente

---

## Códigos de Error

| Código | Significado | Solución |
|--------|-------------|----------|
| 200 | Éxito | Ninguna |
| 400 | Problema no lineal o formato inválido | Revisa el formato del input |
| 401 | API key faltante | Proporciona groq_api_key o configura .env |
| 500 | Error interno | Revisa los logs del servidor |

---

## Variables de Entorno Requeridas

```bash
GROQ_API_KEY=tu-api-key-aqui
GROQ_MODEL=openai/gpt-oss-20b
```

Si no configuras GROQ_API_KEY, debe enviarse en cada request.
"""

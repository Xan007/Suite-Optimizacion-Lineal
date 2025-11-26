# Backend - Suite de Optimización Lineal

Aplicación web con Django para análisis automático de problemas de optimización lineal usando Groq y SymPy.

## 🚀 Características

- ✅ Análisis de problemas usando **Groq AI**
- ✅ Extracción automática de modelos matemáticos con **SymPy**
- ✅ Generación de expresiones matemáticas editables
- ✅ Manejo seguro de API keys (con/sin encriptación RSA)
- ✅ Documentación automática con **Swagger UI**

## 📋 Requisitos

- Python 3.10+
- pip o conda

## 🔧 Instalación

### 1. Crear entorno virtual
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias
```powershell
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Edita `.env` en la raíz del backend:

```env
PROJECT_NAME="Suite de Optimización Lineal"
GROQ_API_KEY="tu-api-key-aqui"
GROQ_MODEL="mixtral-8x7b-32768"
ENVIRONMENT="local"
```

**Obtén tu API key en:** https://console.groq.com

### 4. Ejecutar servidor (Django)
```powershell
cd backend
python manage.py migrate
```

El servidor estará disponible en: `http://localhost:8000` y la interfaz básica en `/`.

## 📚 Documentación

La documentación automática Swagger ya no está incluida por defecto tras la migración a Django. Puedes integrarla con drf-spectacular o Django REST Framework si es necesario.

## 🔌 Endpoints

### Health Check
```
GET /api/v1/test/
```

### Analizar Problema
```
POST /api/v1/analyze/
```

**Request:**
```json
{
  "problem": "Una fábrica produce dos productos A y B...",
  "api_key": "optional-user-key",
  "groq_model": "mixtral-8x7b-32768"
}
```

**Response:**
```json
{
  "raw_analysis": "Análisis de Groq...",
  "mathematical_model": {
    "objective_function": "3*x + 2*y",
    "constraints": ["x + y <= 10", "x >= 0", "y >= 0"],
    "variables": ["x", "y"],
    "model_type": "linear"
  },
  "representations": {
    "canonical": {...},
    "standard": {...},
    "matrix": {...},
    "dual": {...}
  },
  "tokens_used": 156,
  "groq_model": "mixtral-8x7b-32768"
}
```

### Obtener Representaciones
```
POST /api/v1/analyze/get-representations
```

### Validar Modelo
```
POST /api/v1/analyze/validate-model
```

## 🏗️ Estructura del Proyecto (Django)

```
backend/
├── manage.py
├── optiline/                # Proyecto Django (settings, urls, wsgi, asgi)
├── webapp/                  # App Django con vistas y templates
│   ├── views.py             # Vistas equivalentes a endpoints previos
│   ├── urls.py              # Rutas /api/v1/... mantenidas
│   ├── templates/
│   │   └── index.html       # Interfaz básica
├── app/                     # Lógica existente (NO modificada)
│   ├── core/
│   ├── services/
│   ├── schemas/
│   └── api/ (legacy FastAPI, puede eliminarse si no se usa)
├── requirements.txt
├── .env
└── README.md
```

## 🔒 Seguridad

### API Keys del Usuario
- **Opción 1**: El usuario puede pasar su propia API key en cada solicitud
- **Opción 2**: Se usa la API key por defecto del `.env` si no se proporciona una

### Variables Sensibles
Nunca commitear `.env` a Git (ya está en `.gitignore`)

## 🧪 Testing

```powershell
pytest tests/ -v
```

## 📊 Representaciones del Modelo

El backend genera automáticamente 4 representaciones del modelo:

### 1. Forma Canónica
Representación original del problema con operadores naturales (<=, >=, =).

### 2. Forma Estándar
Transformación lista para métodos como Simplex:
- Objetivo: maximización
- Restricciones: igualdades (=)
- Variables de holgura/exceso añadidas
- Todas las variables >= 0

### 3. Forma Matricial
Representación matricial Ax = b:
- Matriz A: coeficientes de restricciones
- Vector b: términos independientes
- Vector c: coeficientes objetivo
- Incluye LaTeX para visualización

### 4. Problema Dual
Generación automática del problema dual:
- Si primal: max c·x s.a. Ax <= b, x >= 0
- Dual: min b·y s.a. A^T·y >= c, y >= 0
- Dualidad débil y fuerte aplicables

## 📝 Notas

- SymPy se usa para parsear y validar expresiones matemáticas
- Groq retorna análisis en JSON estructurado
- El modelo matemático se puede editar manualmente y se re-valida con SymPy

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o PR.

## 📄 Licencia

MIT

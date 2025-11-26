# Copilot Instructions - Suite de Optimización Lineal

## Architecture Overview

This is a **Django web application** (not FastAPI despite some legacy code) that analyzes linear optimization problems using Groq AI and SymPy. The system has three main layers:

1. **API Layer** (`app/api/routes/`) - Django views in `webapp/views.py` handle HTTP requests
2. **Service Layer** (`app/services/`) - Core business logic for problem analysis and transformation
3. **Integration Layer** (`app/core/`) - Configuration, logging, Groq client, and security utilities

**Key Components:**

- **AnalyzeService** (`app/services/analyze_service.py`) - Orchestrates Groq analysis + SymPy extraction
- **ProblemProcessor** (`app/services/problem_processor.py`) - Normalizes raw Groq JSON into SymPy expressions
- **ProblemTransformer** (`app/services/problem_transformer.py`) - Generates 4 problem representations (canonical, standard, matrix, dual)
- **GroqClient** (`app/core/groq_client.py`) - Wrapper around Groq API supporting text/images
- **SolverService** (`app/services/solver_service.py`) - Solves linear programs (Simplex method via PuLP)

## Data Flow

1. User sends problem text (or image) to `/api/v1/analyze/`
2. **AnalyzeService** calls **GroqClient** with structured prompt (from `app/prompts/`)
3. Groq returns JSON: `{is_linear, objective, constraints, variables, ...}`
4. **ProblemProcessor** converts to SymPy expressions (Symbol objects, validation)
5. **ProblemTransformer** generates 4 representations
6. **MathematicalModel** (Pydantic schema) returned to frontend

## Critical Patterns & Conventions

### 1. Problem Structure

Problems are normalized to this structure (see `problem_processor.py`):

```python
{
    'variables': {Symbol('x1'): 'description', Symbol('x2'): 'description'},
    'constraints': [(expr, sign, rhs, original_op), ...],  # original_op preserves pre-normalization operator
    'objective_function': SymPy expression,
    'objective': 'max' or 'min'
}
```

- **Constraints use normalized signs** internally: `<=`, `>=`, `=`
- **original_op** tracks the operator before transformation (important for forms)
- All expressions are SymPy objects, not strings

### 2. Configuration & Environment

- Settings from `.env` (one level above `backend/`): `GROQ_API_KEY`, `GROQ_MODEL`, `PROJECT_NAME`
- Fallback models in `optiline/settings.py`: `openai/gpt-oss-20b` (default), `mixtral-8x7b-32768`
- RSA encryption for API keys optional (`.keys/private_key.pem`, `.keys/public_key.pem`)

### 3. Request/Response Cycle

- **Input**: `AnalyzeRequest` (Pydantic) with `problem`, optional `api_key`, optional `groq_model`
- **Output**: `AnalyzeResponse` contains:
  - `raw_analysis` - Raw Groq response
  - `mathematical_model` - `MathematicalModel` instance
  - `representations` - `ProblemRepresentations` with 4 forms
  - `tokens_used`, `groq_model` - Metadata

### 4. Django vs Legacy FastAPI Code

- **Active**: Django (`optiline/settings.py`, `webapp/views.py`, `webapp/urls.py`)
- **Inactive**: FastAPI code in `app/api/routes/analyze.py` and `app/main.py` (kept for reference but not used)
- All endpoints exposed via Django views → Pydantic schemas still used for validation

### 5. Expression Handling

- SymPy expressions are **cleaned** before returning (see `clean_sympy_expression` in `expression_utils.py`)
- When creating expressions from strings: use `insert_multiplication()` to handle implicit multiplication (`2x` → `2*x`)
- LaTeX generation: use SymPy's `latex()` function for matrix and expression display

### 6. API Endpoints (via Django)

```
GET  /api/v1/test/                          # Health check
POST /api/v1/analyze/                       # Main analysis endpoint
POST /api/v1/analyze/validate-model         # Validate MathematicalModel with SymPy
POST /api/v1/analyze/get-representations    # Get 4 representations for existing model
POST /api/v1/analyze/analyze-image          # Analyze problem from image
POST /api/v1/analyze/solve                  # Solve using Simplex (PuLP)
```

## Development Workflow

### Local Setup

```powershell
# Backend (in backend/ directory)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create .env with Groq API key
echo 'GROQ_API_KEY=your-key' > ../.env

# Run Django
python manage.py migrate
python manage.py runserver  # http://localhost:8000
```

### Testing New Features

- Use `app/prompts/` to define prompt templates (referenced by name in `AnalyzeService`)
- Add new constraints/representations to `ProblemTransformer` (follows Taha's textbook methodology)
- Validate SymPy parsing with `ProblemProcessor.process()` before adding new variable types

### Adding New Problem Representations

1. Add method to `ProblemTransformer` (e.g., `to_new_form()`)
2. Update `get_all_representations()` to include it
3. Add field to `ProblemRepresentations` schema
4. Include in `AnalyzeResponse.representations`

## Integration Points

### External APIs

- **Groq** - Set model via `GROQ_MODEL` in `.env`. Supports text + vision models
- Vision models: `llama-3.2-11b-vision-preview` (default), fallback available

### Libraries

- **SymPy** - Mathematical expressions, equation solving
- **PuLP** - Linear program solver (Simplex backend)
- **Pydantic** - Schema validation (still used with Django)
- **python-dotenv** - Environment configuration

### Security

- API keys: user can pass per-request or use `.env` default
- CORS configured in `optiline/settings.py` (Django middleware)
- CSRF exempt on analysis endpoints (stateless API)

## Key Files to Understand

| File                                  | Purpose                                                     |
| ------------------------------------- | ----------------------------------------------------------- |
| `app/services/analyze_service.py`     | Orchestration: Groq → SymPy → Response                      |
| `app/services/problem_processor.py`   | Normalizes raw JSON to SymPy problem                        |
| `app/services/problem_transformer.py` | Generates canonical/standard/matrix/dual forms              |
| `app/core/groq_client.py`             | Groq API client with text + image support                   |
| `app/schemas/analyze_schema.py`       | Pydantic models (AnalyzeRequest/Response/MathematicalModel) |
| `webapp/views.py`                     | Django endpoints (HTTP handlers)                            |
| `app/prompts/basic_analysis.py`       | Prompt templates for Groq                                   |
| `optiline/settings.py`                | Django configuration                                        |

## Common Tasks

**Analyze a new problem type:**

1. Add prompting logic to `app/prompts/` (or extend existing)
2. Update `ProblemProcessor` if new variable/constraint syntax needed
3. Test with `AnalyzeService.analyze_problem(text)`

**Debug Groq response issues:**

- Check raw JSON in `raw_analysis` field of response
- Log Groq calls in `GroqClient.chat()` - see `app/core/logger.py`
- Verify `is_linear` flag in parsed response (non-linear problems rejected)

**Fix SymPy parsing errors:**

- Check constraint syntax in `ProblemProcessor._normalize_constraint()`
- Use `clean_sympy_expression()` for output formatting
- Test expression creation with `insert_multiplication()` first

**Add new solver method:**

- Update `SolverService.solve()` to handle new method parameter
- Implement using PuLP (LpProblem, LpVariable, solver selection)
- Return consistent result format

## Deployment Notes

- No database models used (SQLite but empty)
- Stateless API design - no session/state persistence needed
- `.env` must contain valid `GROQ_API_KEY` before startup
- Django migrations optional (no schema changes needed)

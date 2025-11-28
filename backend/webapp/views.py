import json
from typing import Optional, Dict, Any, Callable
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import sympy as sp

from app.services.analyze_service import AnalyzeService
from app.schemas.analyze_schema import AnalyzeRequest, AnalyzeResponse, MathematicalModel
from app.core.config import settings as fastapi_settings
from app.core.logger import logger
from app.utils.latex_utils import (
    format_expression_to_latex,
    convert_constraint_to_latex,
    generate_nonnegative_latex_conditions
)


class SymPyEncoder(json.JSONEncoder):
    """Encoder personalizado para serializar objetos SymPy a strings."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (sp.Basic, sp.Symbol)):
            return str(obj)
        return super().default(obj)


def _is_nonnegative_constraint(constraint_str: str, variables: Dict[str, str]) -> bool:
    """Verifica si una restricción es de no-negatividad."""
    return any(f"{v} >= 0" in constraint_str.lower() or f"{v}<= 0" in constraint_str.lower() 
               for v in variables.keys())


def _build_canonical_form_with_latex(model: MathematicalModel) -> Dict[str, Any]:
    """Construye representación canónica con LaTeX sin duplicación de no-negatividad."""
    constraints = [c for c in model.constraints if not _is_nonnegative_constraint(c, model.variables)]
    return {
        "form": "canonical",
        "objective": model.objective,
        "objective_function_latex": format_expression_to_latex(model.objective_function),
        "objective_function": model.objective_function,
        "constraints_latex": [convert_constraint_to_latex(c) or c for c in constraints],
        "constraints": constraints,
        "non_negativity_latex": generate_nonnegative_latex_conditions(model.variables),
        "variables": model.variables
    }


def _handle_json_request(request: HttpRequest, schema_class: type) -> Optional[Any]:
    """Helper para parsear JSON y validar con schema."""
    try:
        return schema_class(**json.loads(request.body.decode('utf-8')))
    except Exception as e:
        logger.error(f"Error parseando JSON: {e}")
        raise ValueError(f"JSON inválido: {e}")


def _json_response(data: Dict[str, Any], status: int = 200, **kwargs) -> JsonResponse:
    """Helper para retornar respuestas JSON con SymPyEncoder."""
    return JsonResponse(data, status=status, encoder=SymPyEncoder, **kwargs)


def _add_latex_to_response(response_dict: Dict[str, Any], model: MathematicalModel) -> None:
    """Agrega datos LaTeX a respuesta existente."""
    canonical_latex = _build_canonical_form_with_latex(model)
    if response_dict.get("mathematical_model"):
        response_dict["mathematical_model"].update({
            "objective_function_latex": canonical_latex.get("objective_function_latex"),
            "constraints_latex": canonical_latex.get("constraints_latex"),
            "non_negativity_latex": canonical_latex.get("non_negativity_latex")
        })
    if response_dict.get("representations", {}).get("canonical"):
        response_dict["representations"]["canonical"].update(canonical_latex)


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    """Renderiza la página principal."""
    return render(request, 'index.html')


@require_GET
def test(request: HttpRequest) -> JsonResponse:
    """Endpoint de prueba."""
    return _json_response({"message": "Test done"})


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """Verifica el estado de la aplicación."""
    return _json_response(True, safe=False)


@csrf_exempt
@require_POST
def analyze_problem(request: HttpRequest) -> JsonResponse:
    """Analiza un problema de optimización lineal."""
    try:
        analyze_req = _handle_json_request(request, AnalyzeRequest)
        api_key = analyze_req.api_key or fastapi_settings.GROQ_API_KEY
        if not api_key:
            return _json_response({"detail": "API key requerida"}, status=401)
        
        service = AnalyzeService(groq_api_key=api_key)
        response = service.analyze_problem(
            problem_text=analyze_req.problem,
            groq_model=analyze_req.groq_model or fastapi_settings.GROQ_MODEL,
            prompt_name='basic'
        )
        
        if not response:
            return _json_response({"detail": "Error al procesar el problema"}, status=500)
        
        service.validate_model_with_sympy(response.mathematical_model)
        representations_dict = service.get_problem_representations()
        if representations_dict:
            from app.schemas.analyze_schema import ProblemRepresentations
            response.representations = ProblemRepresentations(**representations_dict)
        
        response_dict = json.loads(response.model_dump_json())
        _add_latex_to_response(response_dict, response.mathematical_model)
        
        return _json_response(response_dict)
    except Exception as e:
        logger.error(f"Error en analyze_problem: {e}")
        return _json_response({"detail": "Error interno del servidor"}, status=500)


@csrf_exempt
@require_POST
def validate_model(request: HttpRequest) -> JsonResponse:
    """Valida un modelo matemático con SymPy."""
    try:
        math_model = _handle_json_request(request, MathematicalModel)
        service = AnalyzeService(groq_api_key='dummy')
        is_valid = service.validate_model_with_sympy(math_model)
        return _json_response({
            'is_valid': is_valid,
            'sympy_expressions': service.generate_sympy_expression(math_model),
            'message': 'Modelo validado correctamente' if is_valid else 'Error en validación'
        })
    except Exception as e:
        logger.error(f"Error validando modelo: {e}")
        return _json_response({'detail': f'Error en validación: {e}'}, status=400)


@csrf_exempt
@require_POST
def get_representations(request: HttpRequest) -> JsonResponse:
    """Genera todas las representaciones de un modelo."""
    try:
        model_dict = json.loads(request.body.decode('utf-8'))
        from app.services.problem_transformer import ProblemTransformer
        representations = ProblemTransformer(model_dict).get_all_representations()
        return _json_response({'success': True, 'representations': representations})
    except Exception as e:
        logger.error(f"Error generando representaciones: {e}")
        return _json_response({'detail': f'Error al generar representaciones: {e}'}, status=400)


@csrf_exempt
@require_POST
def analyze_problem_from_image(request: HttpRequest) -> JsonResponse:
    """Analiza un problema desde una imagen."""
    try:
        if 'file' not in request.FILES:
            return _json_response({'detail': 'Imagen requerida'}, status=400)
        
        image_file = request.FILES['file']
        if not image_file.content_type or not image_file.content_type.startswith('image/'):
            return _json_response({'detail': 'El archivo debe ser una imagen'}, status=400)
        
        api_key = request.POST.get('api_key') or fastapi_settings.GROQ_API_KEY
        if not api_key:
            return _json_response({'detail': 'API key requerida'}, status=401)
        
        service = AnalyzeService(groq_api_key=api_key)
        response = service.analyze_problem_from_image(
            image_data=image_file.read(),
            problem_description=request.POST.get('problem_description'),
            groq_model=None,
            prompt_name='basic'
        )
        
        if not response:
            return _json_response({'detail': 'Error al procesar la imagen'}, status=500)
        
        service.validate_model_with_sympy(response.mathematical_model)
        representations_dict = service.get_problem_representations()
        if representations_dict:
            from app.schemas.analyze_schema import ProblemRepresentations
            response.representations = ProblemRepresentations(**representations_dict)
        
        return _json_response(json.loads(response.model_dump_json()))
    except Exception as e:
        logger.error(f"Error en analyze_problem_from_image: {e}")
        return _json_response({'detail': 'Error interno del servidor'}, status=500)


@csrf_exempt
@require_POST
def solve_model(request: HttpRequest) -> JsonResponse:
    """Resuelve un modelo matemático con el método seleccionado."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        model_dict = payload.get('model')
        if not model_dict:
            return _json_response({'detail': "Falta campo 'model' en payload"}, status=400)
        
        model = MathematicalModel(**model_dict)
        method = payload.get('method', 'simplex')
        
        # Validación: problemas de minimización solo pueden usar dual_simplex, big_m o interior_point
        if model.objective == "min" and method not in ["dual_simplex", "big_m", "interior_point"]:
            return _json_response({
                'success': False,
                'detail': f"Los problemas de minimización solo pueden resolverse con el Método Simplex Dual, el Método de la Gran M o el Método de Punto Interior. El método '{method}' no está disponible para minimización.",
                'allowed_methods': ["dual_simplex", "big_m", "interior_point"],
                'objective_type': 'min'
            }, status=400)
        
        from app.services.solver_service import SolverService
        result = SolverService().solve(model, method=method)
        
        return _json_response({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"Error en solve_model: {str(e)}", exc_info=True)
        return _json_response({'detail': str(e)}, status=500)

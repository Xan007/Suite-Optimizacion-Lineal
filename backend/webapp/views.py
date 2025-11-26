import json
from typing import Optional, Dict, Any
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import sympy as sp

# Import existing logic without modification
from app.services.analyze_service import AnalyzeService
from app.schemas.analyze_schema import AnalyzeRequest, AnalyzeResponse, MathematicalModel
from app.core.config import settings as fastapi_settings
from app.core.logger import logger


def _format_expression_latex(expr_str: str) -> str:
    """Convierte una expresión a LaTeX legible."""
    try:
        expr = sp.sympify(expr_str)
        return sp.latex(expr)
    except:
        return expr_str


def _generate_canonical_form_latex(model: MathematicalModel) -> Dict[str, Any]:
    """
    Genera una representación del modelo canónico con LaTeX.
    
    Formato:
    - Objetivo: LaTeX
    - Restricciones: LaTeX con operadores
    - No-negatividad: LaTeX
    """
    latex_model = {
        "form": "canonical",
        "objective": model.objective,
        "objective_function_latex": _format_expression_latex(model.objective_function),
        "objective_function": model.objective_function,
        "constraints_latex": [],
        "constraints": [],
        "non_negativity_latex": [],
        "variables": model.variables
    }
    
    # Procesar restricciones
    for constraint_str in model.constraints:
        latex_model["constraints"].append(constraint_str)
        try:
            # Parsear restricción: "expr1 op expr2" -> LaTeX
            for op in ["<=", ">=", "="]:
                if op in constraint_str:
                    parts = constraint_str.split(op)
                    if len(parts) == 2:
                        lhs_latex = _format_expression_latex(parts[0].strip())
                        rhs_latex = _format_expression_latex(parts[1].strip())
                        op_symbol = r"\leq" if op == "<=" else (r"\geq" if op == ">=" else "=")
                        latex_model["constraints_latex"].append(f"{lhs_latex} {op_symbol} {rhs_latex}")
                    break
        except Exception as e:
            logger.warning(f"Error formateando restricción a LaTeX: {e}")
            latex_model["constraints_latex"].append(constraint_str)
    
    # No-negatividad para cada variable
    for var_name in model.variables.keys():
        latex_model["non_negativity_latex"].append(f"{var_name} \\geq 0")
    
    return latex_model

@require_GET
def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

@require_GET
def test(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"message": "Test done"})

@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    return JsonResponse(True, safe=False)

@csrf_exempt
@require_POST
def analyze_problem(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body.decode('utf-8'))
        analyze_req = AnalyzeRequest(**payload)
        api_key = analyze_req.api_key or fastapi_settings.GROQ_API_KEY
        if not api_key:
            return JsonResponse({"detail": "API key requerida"}, status=401)
        service = AnalyzeService(groq_api_key=api_key)
        response = service.analyze_problem(
            problem_text=analyze_req.problem,
            groq_model=analyze_req.groq_model or fastapi_settings.GROQ_MODEL,
            prompt_name='basic'
        )
        if not response:
            return JsonResponse({"detail": "Error al procesar el problema"}, status=500)
        is_valid = service.validate_model_with_sympy(response.mathematical_model)
        representations_dict = service.get_problem_representations()
        if representations_dict:
            from app.schemas.analyze_schema import ProblemRepresentations
            response.representations = ProblemRepresentations(**representations_dict)
        
        # Agregar formato LaTeX al modelo canónico
        response_dict = json.loads(response.model_dump_json())
        canonical_latex = _generate_canonical_form_latex(response.mathematical_model)
        if response_dict.get("representations") and response_dict["representations"].get("canonical"):
            response_dict["representations"]["canonical"].update(canonical_latex)
        
        return JsonResponse(response_dict, status=200)
    except Exception as e:
        logger.error(f"Error en analyze_problem: {e}")
        return JsonResponse({"detail": "Error interno del servidor"}, status=500)

@csrf_exempt
@require_POST
def validate_model(request: HttpRequest) -> JsonResponse:
    try:
        model_dict = json.loads(request.body.decode('utf-8'))
        math_model = MathematicalModel(**model_dict)
        service = AnalyzeService(groq_api_key='dummy')
        is_valid = service.validate_model_with_sympy(math_model)
        sympy_expressions = service.generate_sympy_expression(math_model)
        return JsonResponse({
            'is_valid': is_valid,
            'sympy_expressions': sympy_expressions,
            'message': 'Modelo validado correctamente' if is_valid else 'Error en validación'
        })
    except Exception as e:
        logger.error(f"Error validando modelo: {e}")
        return JsonResponse({'detail': f'Error en validación: {e}'}, status=400)

@csrf_exempt
@require_POST
def get_representations(request: HttpRequest) -> JsonResponse:
    try:
        model_dict = json.loads(request.body.decode('utf-8'))
        from app.services.problem_transformer import ProblemTransformer
        transformer = ProblemTransformer(model_dict)
        representations = transformer.get_all_representations()
        return JsonResponse({'success': True, 'representations': representations})
    except Exception as e:
        logger.error(f"Error generando representaciones: {e}")
        return JsonResponse({'detail': f'Error al generar representaciones: {e}'}, status=400)

@csrf_exempt
@require_POST
def analyze_problem_from_image(request: HttpRequest) -> JsonResponse:
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'detail': 'Imagen requerida'}, status=400)
        image_file = request.FILES['file']
        problem_description = request.POST.get('problem_description')
        api_key = request.POST.get('api_key') or fastapi_settings.GROQ_API_KEY
        if not api_key:
            return JsonResponse({'detail': 'API key requerida'}, status=401)
        image_content = image_file.read()
        if not image_file.content_type or not image_file.content_type.startswith('image/'):
            return JsonResponse({'detail': 'El archivo debe ser una imagen'}, status=400)
        service = AnalyzeService(groq_api_key=api_key)
        response = service.analyze_problem_from_image(
            image_data=image_content,
            problem_description=problem_description,
            groq_model=None,
            prompt_name='basic'
        )
        if not response:
            return JsonResponse({'detail': 'Error al procesar la imagen'}, status=500)
        is_valid = service.validate_model_with_sympy(response.mathematical_model)
        representations_dict = service.get_problem_representations()
        if representations_dict:
            from app.schemas.analyze_schema import ProblemRepresentations
            response.representations = ProblemRepresentations(**representations_dict)
        return JsonResponse(json.loads(response.model_dump_json()), status=200)
    except Exception as e:
        logger.error(f"Error en analyze_problem_from_image: {e}")
        return JsonResponse({'detail': 'Error interno del servidor'}, status=500)

@csrf_exempt
@require_POST
def solve_model(request: HttpRequest) -> JsonResponse:
    """Resuelve un modelo matemático con el método seleccionado."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        model_dict = payload.get('model')
        method = payload.get('method', 'simplex')
        
        if not model_dict:
            return JsonResponse({'detail': "Falta campo 'model' en payload"}, status=400)
        
        # Crear modelo matemático
        math_model = MathematicalModel(**model_dict)
        
        # Resolver usando SolverService
        from app.services.solver_service import SolverService
        service = SolverService()
        result = service.solve(math_model, method=method)
        
        return JsonResponse({'success': True, 'result': result}, status=200)
    
    except Exception as e:
        logger.error(f"Error en solve_model: {str(e)}", exc_info=True)
        return JsonResponse({'detail': str(e)}, status=500)

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import Optional

from app.schemas.analyze_schema import AnalyzeRequest, AnalyzeImageRequest, AnalyzeResponse
from app.services.analyze_service import AnalyzeService
from app.core.config import settings
from app.core.logger import logger
from app.api.docs import (
    ANALYZE_ENDPOINT_DOC,
    VALIDATE_MODEL_ENDPOINT_DOC,
    GET_REPRESENTATIONS_ENDPOINT_DOC,
    ANALYZE_IMAGE_ENDPOINT_DOC,
)

router = APIRouter(prefix="/analyze", tags=["analyze"])


def get_api_key(request: AnalyzeRequest) -> str:
    """
    Obtiene la API key del usuario o usa la por defecto del .env.
    
    Args:
        request: Solicitud con API key opcional
        
    Returns:
        API key a usar
        
    Raises:
        HTTPException si no hay API key disponible
    """
    api_key = request.api_key or settings.GROQ_API_KEY
    
    if not api_key:
        logger.error("No se proporcionó API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key requerida (proporciona una o configura GROQ_API_KEY en .env)",
        )
    
    return api_key


@router.post(
    "/", 
    response_model=AnalyzeResponse, 
    status_code=status.HTTP_200_OK,
    description=ANALYZE_ENDPOINT_DOC
)
async def analyze_problem(request: AnalyzeRequest) -> AnalyzeResponse:
    """Análisis Completo de Problema de Optimización Lineal"""
    try:
        logger.info(f"Nueva solicitud de análisis recibida")
        
        # Obtener API key
        api_key = get_api_key(request)
        
        # Crear servicio de análisis
        service = AnalyzeService(groq_api_key=api_key)
        
        # Analizar problema (usa prompt "basic" internamente)
        response = service.analyze_problem(
            problem_text=request.problem,
            groq_model=request.groq_model or settings.GROQ_MODEL,
            prompt_name="basic",
        )
        
        if not response:
            logger.error("El servicio de análisis no retornó respuesta")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar el problema",
            )
        
        # Validar modelo con SymPy
        is_valid = service.validate_model_with_sympy(response.mathematical_model)
        if not is_valid:
            logger.warning("Modelo no validado por SymPy, pero se retorna igualmente")
        
        # Generar todas las representaciones del problema
        representations_dict = service.get_problem_representations()
        if representations_dict:
            from app.schemas.analyze_schema import ProblemRepresentations
            response.representations = ProblemRepresentations(**representations_dict)
        
        logger.info("Análisis completado exitosamente")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint /analyze: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor",
        )


@router.post(
    "/validate-model",
    description=VALIDATE_MODEL_ENDPOINT_DOC
)
async def validate_model(model: dict) -> dict:
    """Validar Modelo Matemático con SymPy"""
    try:
        from app.schemas.analyze_schema import MathematicalModel
        
        math_model = MathematicalModel(**model)
        
        # Usar un servicio temporal para validar
        service = AnalyzeService(groq_api_key="dummy")
        is_valid = service.validate_model_with_sympy(math_model)
        
        sympy_expressions = service.generate_sympy_expression(math_model)
        
        return {
            "is_valid": is_valid,
            "sympy_expressions": sympy_expressions,
            "message": "Modelo validado correctamente" if is_valid else "Error en validación",
        }
        
    except Exception as e:
        logger.error(f"Error validando modelo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en validación: {str(e)}",
        )


@router.post(
    "/get-representations",
    description=GET_REPRESENTATIONS_ENDPOINT_DOC
)
async def get_representations(model: dict) -> dict:
    """Generar Todas las Representaciones de un Modelo"""
    try:
        from app.services.problem_transformer import ProblemTransformer
        
        transformer = ProblemTransformer(model)
        representations = transformer.get_all_representations()
        
        return {
            "success": True,
            "representations": representations
        }
        
    except Exception as e:
        logger.error(f"Error generando representaciones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al generar representaciones: {str(e)}",
        )


@router.post(
    "/analyze-image", 
    response_model=AnalyzeResponse, 
    status_code=status.HTTP_200_OK,
    description=ANALYZE_IMAGE_ENDPOINT_DOC
)
async def analyze_problem_from_image(
    file: UploadFile = File(..., description="Imagen con el problema de optimización"),
    problem_description: Optional[str] = Form(None, description="Descripción adicional del problema"),
    api_key: Optional[str] = Form(None, description="API key del usuario (opcional)"),
    groq_model: Optional[str] = Form(None, description="Modelo de Groq a usar (se ignorará, siempre usa modelo de visión)"),
) -> AnalyzeResponse:
    """Análisis desde Imagen - De Foto a Todas las Representaciones"""
    try:
        logger.info("Nueva solicitud de análisis desde imagen recibida")
        
        # Obtener API key
        api_key = api_key or settings.GROQ_API_KEY
        if not api_key:
            logger.error("No se proporcionó API key")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key requerida",
            )
        
        # Leer contenido de la imagen
        image_content = await file.read()
        
        # Validar que sea una imagen
        if not file.content_type or not file.content_type.startswith("image/"):
            logger.error(f"Tipo de archivo no válido: {file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser una imagen (PNG, JPG, etc.)",
            )
        
        # Crear servicio de análisis
        service = AnalyzeService(groq_api_key=api_key)
        
        # Analizar imagen (SIEMPRE usa modelo de visión, nunca el groq_model del usuario)
        response = service.analyze_problem_from_image(
            image_data=image_content,
            problem_description=problem_description,
            groq_model=None,  # Ignorar groq_model - siempre usar GROQ_VISION_MODEL
            prompt_name="basic",
        )
        
        if not response:
            logger.error("El servicio de análisis no retornó respuesta")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar la imagen",
            )
        
        # Validar modelo con SymPy
        is_valid = service.validate_model_with_sympy(response.mathematical_model)
        if not is_valid:
            logger.warning("Modelo no validado por SymPy, pero se retorna igualmente")
        
        # Generar todas las representaciones del problema
        representations_dict = service.get_problem_representations()
        if representations_dict:
            from app.schemas.analyze_schema import ProblemRepresentations
            response.representations = ProblemRepresentations(**representations_dict)
        
        logger.info("Análisis desde imagen completado exitosamente")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint /analyze-image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor",
        )

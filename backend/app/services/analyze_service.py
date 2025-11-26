import json
import re
from typing import Optional, Dict
import sympy as sp

from app.core.logger import logger
from app.core.config import settings
from app.core.groq_client import GroqClient
from app.schemas.analyze_schema import MathematicalModel, AnalyzeResponse
from app.services.problem_processor import ProblemProcessor
from app.services.problem_transformer import ProblemTransformer
from app.services.solver_service import SolverService
from app.services.expression_utils import clean_sympy_expression
from app.prompts import get_prompt


class AnalyzeService:
    """Servicio de análisis que integra Groq, SymPy y transformaciones."""

    def __init__(self, groq_api_key: str):
        self.groq_client = GroqClient(api_key=groq_api_key)
        self.problem_processor = ProblemProcessor()
        self.solver = SolverService()

    def analyze_problem(
        self,
        problem_text: str,
        groq_model: Optional[str] = None,
        prompt_name: str = "basic",
    ) -> Optional[AnalyzeResponse]:
        """
        Analiza un problema usando Groq y extrae el modelo matemático con SymPy.
        
        Args:
            problem_text: Descripción del problema
            groq_model: Modelo de Groq a usar
            prompt_name: Nombre del prompt ("standard", "detailed", etc.)
            
        Returns:
            AnalyzeResponse con análisis y modelo matemático, o None si no es lineal
        """
        try:
            # Usar modelo del config si no se especifica
            model_to_use = groq_model or settings.GROQ_MODEL
            
            logger.info(f"Iniciando análisis del problema (prompt: {prompt_name})...")
            self.groq_client.model = model_to_use

            # Obtener el prompt según el nombre
            prompt_template = get_prompt(prompt_name)
            prompt = prompt_template.format(problem_text=problem_text)

            # Llamar a Groq para obtener respuesta
            groq_result = self.groq_client.chat(prompt)
            if not groq_result.get("success"):
                logger.error(f"Error en Groq: {groq_result.get('error')}")
                return None

            raw_analysis = groq_result["content"].strip()

            # Parsear JSON de la respuesta
            parsed_data = self._parse_response_json(raw_analysis)
            if not parsed_data:
                logger.error("No se pudo parsear la respuesta como JSON")
                return None

            # Validar linealidad
            is_linear = parsed_data.get("is_linear", True)
            if not is_linear or "error" in parsed_data:
                logger.warning("El problema no es lineal")
                return None

            logger.info("Procesando problema con SymPy...")

            # Procesar con ProblemProcessor
            self.problem_processor.set_raw_problem(parsed_data)
            self.problem_processor.process()

            # Extraer modelo matemático usando DATOS ORIGINALES de Groq
            math_model = self._extract_mathematical_model(
                self.problem_processor.problem, 
                parsed_data,  # Pasar datos originales de Groq
                problem_text
            )

            # Crear respuesta
            response = AnalyzeResponse(
                raw_analysis=raw_analysis,
                mathematical_model=math_model,
                groq_model=model_to_use,
                is_linear=True,
            )

            # Determinar métodos aplicables y razones por las que no aplican
            try:
                suggested, not_applicable = self.solver.determine_applicable_methods(math_model)
                response.suggested_methods = suggested
                response.methods_not_applicable = not_applicable
            except Exception:
                # no es crítico
                response.suggested_methods = []
                response.methods_not_applicable = {}

            logger.info("Análisis completado exitosamente")
            return response

        except Exception as e:
            logger.error(f"Error en analyze_problem: {str(e)}")
            return None

    def _parse_response_json(self, response_text: str) -> Optional[Dict]:
        """
        Extrae JSON válido de la respuesta de Groq.
        
        Args:
            response_text: Texto de respuesta de Groq
            
        Returns:
            Dict parseado o None si hay error
        """
        try:
            # Remover bloques de código markdown si existen
            if response_text.startswith("```"):
                parts = response_text.split("```")
                for part in parts:
                    if part.strip().startswith("{"):
                        response_text = part.strip()
                        break

            parsed = json.loads(response_text)
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON: {str(e)}")
            return None

    def _extract_mathematical_model(
        self, 
        processed_problem: Dict, 
        raw_groq_data: Dict,
        original_problem: str = ""
    ) -> MathematicalModel:
        """
        Extrae el modelo matemático del problema procesado.
        Utiliza las RESTRICCIONES ORIGINALES de Groq (sin normalizar).
        Limpia solo las expresiones SymPy (sin cambiar lógica ni signos).
        
        Args:
            processed_problem: Problema procesado por ProblemProcessor (para función objetivo y variables)
            raw_groq_data: Datos originales desde Groq (para restricciones sin modificar)
            original_problem: Texto del problema original
            
        Returns:
            MathematicalModel con expresiones limpias pero respetando la IA
        """
        try:
            objective_fn = processed_problem.get("objective_function", "")
            objective = processed_problem.get("objective", "max")
            variables = processed_problem.get("variables", {})

            # Convertir variables SymPy a strings CON sus descripciones
            variables_dict = {str(var): desc for var, desc in variables.items()}

            # USAR RESTRICCIONES ORIGINALES DE GROQ sin modificarlas
            raw_constraints = raw_groq_data.get("constraints", [])
            constraints = []
            
            for constraint_str in raw_constraints:
                # Solo limpiar la expresión SymPy, sin cambiar lógica ni signos
                cleaned = clean_sympy_expression(constraint_str)
                constraints.append(cleaned)

            return MathematicalModel(
                objective_function=clean_sympy_expression(str(objective_fn)),  # Limpiar función objetivo
                objective=objective,
                constraints=constraints,
                variables=variables_dict,
                context=raw_groq_data.get("context", ""),
            )

        except Exception as e:
            logger.error(f"Error extrayendo modelo: {str(e)}")
            return MathematicalModel(
                objective_function="",
                objective="max",
                constraints=[],
                variables={},
                context="",
            )

    def validate_model_with_sympy(self, model: MathematicalModel) -> bool:
        """
        Valida el modelo matemático usando SymPy.
        
        Args:
            model: Modelo matemático a validar
            
        Returns:
            True si el modelo es válido
        """
        try:
            logger.info("Validando modelo con SymPy...")

            # Crear símbolos para las variables (ahora es Dict)
            symbols_dict = {var: sp.Symbol(var) for var in model.variables.keys()}

            # Parsear la función objetivo
            if model.objective_function:
                objective_str = model.objective_function
                objective = sp.sympify(objective_str, locals=symbols_dict)
                logger.info(f"Función objetivo parseada: {objective}")

            # Parsear restricciones
            for constraint_str in model.constraints:
                logger.debug(f"Validando restricción: {constraint_str}")

            logger.info("Modelo validado correctamente")
            return True

        except Exception as e:
            logger.error(f"Error al validar modelo con SymPy: {str(e)}")
            return False

    def generate_sympy_expression(self, model: MathematicalModel) -> Optional[dict]:
        """
        Genera expresiones SymPy para el modelo matemático.
        
        Args:
            model: Modelo matemático
            
        Returns:
            dict con expresiones SymPy en formato string
        """
        try:
            symbols_dict = {var: sp.Symbol(var) for var in model.variables.keys()}

            # Función objetivo
            objective = sp.sympify(model.objective_function, locals=symbols_dict)

            # Restricciones
            constraints_sympified = []
            for constraint_str in model.constraints:
                try:
                    constraint_expr = sp.sympify(constraint_str, locals=symbols_dict)
                    constraints_sympified.append(clean_sympy_expression(str(constraint_expr)))
                except Exception as e:
                    logger.warning(f"Error parseando restricción: {str(e)}")
                    constraints_sympified.append(constraint_str)

            return {
                "objective": clean_sympy_expression(str(objective)),
                "constraints": constraints_sympified,
                "variables": model.variables,
            }

        except Exception as e:
            logger.error(f"Error generando expresiones SymPy: {str(e)}")
            return None

    def get_problem_representations(self) -> Optional[Dict]:
        """
        Genera todas las representaciones del problema procesado.
        
        Returns:
            dict con formas canónica, estándar, matricial y dual
        """
        try:
            if not self.problem_processor.problem:
                logger.warning("No hay problema procesado")
                return None

            transformer = ProblemTransformer(self.problem_processor.problem)
            return transformer.get_all_representations()

        except Exception as e:
            logger.error(f"Error generando representaciones: {str(e)}")
            return None

    def analyze_problem_from_image(
        self,
        image_data: bytes,
        problem_description: Optional[str] = None,
        groq_model: Optional[str] = None,
        prompt_name: str = "basic",
    ) -> Optional[AnalyzeResponse]:
        """
        Analiza un problema desde una imagen usando Groq vision.
        
        Args:
            image_data: Bytes de la imagen
            problem_description: Descripción adicional del problema (opcional)
            groq_model: Modelo de Groq a usar
            prompt_name: Nombre del prompt ("basic", "detailed", etc.)
            
        Returns:
            AnalyzeResponse con análisis y modelo matemático, o None si no es lineal
        """
        try:
            # OBLIGATORIAMENTE usar modelo de visión para imágenes
            # Usar GROQ_VISION_MODEL primero, si falla usar GROQ_VISION_MODEL_FALLBACK
            vision_model = settings.GROQ_VISION_MODEL
            
            logger.info(f"Iniciando análisis desde imagen con modelo: {vision_model}...")
            self.groq_client.model = vision_model

            # Obtener el prompt según el nombre
            prompt_template = get_prompt(prompt_name)
            
            # Construir mensaje para la imagen
            base_prompt = "Analiza la imagen que contiene un problema de optimización lineal. Extrae la información y responde en JSON."
            if problem_description:
                base_prompt += f"\n\nContexto adicional: {problem_description}"
            
            # Luego agregar el formato del prompt
            user_prompt = base_prompt + "\n\n" + prompt_template.split("Problema a analizar:")[0] + "Responde en JSON con el formato requerido."

            # Llamar a Groq con la imagen
            groq_result = self.groq_client.chat(
                user_prompt,
                images=[image_data]
            )
            if not groq_result.get("success"):
                logger.error(f"Error en Groq: {groq_result.get('error')}")
                # Si falla el modelo principal, intentar con fallback
                logger.warning(f"Intentando con modelo fallback: {settings.GROQ_VISION_MODEL_FALLBACK}")
                self.groq_client.model = settings.GROQ_VISION_MODEL_FALLBACK
                groq_result = self.groq_client.chat(
                    user_prompt,
                    images=[image_data]
                )
                if not groq_result.get("success"):
                    logger.error(f"Error en Groq fallback: {groq_result.get('error')}")
                    return None

            raw_analysis = groq_result["content"].strip()

            # Parsear JSON de la respuesta
            parsed_data = self._parse_response_json(raw_analysis)
            if not parsed_data:
                logger.error("No se pudo parsear la respuesta como JSON")
                return None

            # Validar linealidad
            is_linear = parsed_data.get("is_linear", True)
            if not is_linear or "error" in parsed_data:
                logger.warning("El problema no es lineal")
                return None

            logger.info("Procesando problema con SymPy...")

            # Procesar con ProblemProcessor
            self.problem_processor.set_raw_problem(parsed_data)
            self.problem_processor.process()

            # Extraer modelo matemático usando DATOS ORIGINALES de Groq
            math_model = self._extract_mathematical_model(
                self.problem_processor.problem,
                parsed_data,  # Pasar datos originales de Groq
                problem_description or "Problema analizado desde imagen"
            )

            # Crear respuesta
            response = AnalyzeResponse(
                raw_analysis=raw_analysis,
                mathematical_model=math_model,
                groq_model=vision_model,
                is_linear=True,
            )

            # Determinar métodos aplicables y razones por las que no aplican
            try:
                suggested, not_applicable = self.solver.determine_applicable_methods(math_model)
                response.suggested_methods = suggested
                response.methods_not_applicable = not_applicable
            except Exception:
                response.suggested_methods = []
                response.methods_not_applicable = {}

            logger.info("Análisis desde imagen completado exitosamente")
            return response

        except Exception as e:
            logger.error(f"Error en analyze_problem_from_image: {str(e)}")
            return None

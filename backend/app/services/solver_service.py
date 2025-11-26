from typing import Dict, List, Optional, Tuple, Any
import sympy as sp

from app.schemas.analyze_schema import MathematicalModel
from app.core.logger import logger

try:
    import pulp
except Exception:
    pulp = None


class SolverService:
    """Servicio para determinar métodos aplicables y ejecutar la resolución."""

    def __init__(self):
        pass

    def determine_applicable_methods(self, model: MathematicalModel) -> Tuple[List[str], Dict[str, str]]:
        """
        Devuelve lista ordenada de métodos sugeridos y diccionario de métodos no aplicables con razones.
        """
        suggested: List[str] = []
        not_applicable: Dict[str, str] = {}

        # Verificar linealidad rápida: comprobar que todas las expresiones son lineales
        try:
            symbols = {name: sp.Symbol(name, real=True) for name in model.variables.keys()}

            # Objective
            try:
                obj = sp.sympify(model.objective_function, locals=symbols)
            except Exception as e:
                not_applicable["simplex"] = "Función objetivo no parseable como expresión lineal"
                not_applicable["graphical"] = "Función objetivo no parseable"
                return [], not_applicable

            # check linearity function
            def is_linear_expr(expr: sp.Expr) -> bool:
                # degree in each symbol must be <= 1 and no nonlinear functions
                if expr.is_Number:
                    return True
                for s in expr.free_symbols:
                    if sp.degree(expr, s) is None:
                        return False
                    if sp.degree(expr, s) > 1:
                        return False
                # also reject non-polynomial terms
                if expr.has(sp.sin, sp.cos, sp.exp, sp.log, sp.Pow):
                    return False
                return True

            if not is_linear_expr(obj):
                not_applicable["simplex"] = "Función objetivo no lineal"
                not_applicable["graphical"] = "Función objetivo no lineal"
                return [], not_applicable

            # Constraints
            constraints = model.constraints or []
            parsed_constraints = []
            for c in constraints:
                try:
                    rel = sp.sympify(c, locals=symbols, evaluate=False)
                    parsed_constraints.append(rel)
                except Exception:
                    not_applicable["simplex"] = f"Restricción no parseable: {c}"
                    return [], not_applicable

            # Check all constraints linear
            for rel in parsed_constraints:
                # If relational, check lhs and rhs linear
                if hasattr(rel, 'lhs') and hasattr(rel, 'rhs'):
                    if not is_linear_expr(rel.lhs) or not is_linear_expr(rel.rhs):
                        not_applicable["simplex"] = "Al menos una restricción no es lineal"
                        break
                else:
                    # expression without relation - treat as non-applicable
                    not_applicable["simplex"] = "Formato de restricción inesperado"
                    break

            # If simplex not flagged as non-applicable, add it
            if "simplex" not in not_applicable:
                suggested.append("simplex")

            # Graphical: only when number of variables <= 2
            if len(model.variables.keys()) <= 2:
                suggested.append("graphical")
            else:
                not_applicable["graphical"] = "Más de 2 variables, no aplicable para método gráfico"

            # Dual: applicable when matrix form has structural constraints
            # Conservative approach: if there's at least one structural constraint (rhs != 0 or non-neg) allow dual
            has_structural = any((hasattr(rel, 'lhs') and hasattr(rel, 'rhs') and abs(float(rel.rhs)) > 1e-9) for rel in parsed_constraints) if parsed_constraints else False
            if has_structural:
                suggested.append("dual")
            else:
                not_applicable["dual"] = "No hay restricciones estructurales suficientes para construir dual"

            # Big M: applicable if there are >= or = constraints (that may require artificial variables)
            needs_big_m = any((hasattr(rel, 'rel_op') and ('>=' in rel.rel_op or '=' in rel.rel_op)) or (str(rel).find('>=')!=-1 or str(rel).find('=')!=-1 and str(rel).find('<=')==-1) for rel in parsed_constraints)
            # fallback simpler check: presence of equality or '>=' substring
            if any(('>=' in c or '==' in c or '=' in c and '<=' not in c) for c in constraints):
                suggested.append("big_m")
            else:
                not_applicable["big_m"] = "No hay restricciones >= ni = que requieran variables artificiales"

            return suggested, not_applicable

        except Exception as e:
            logger.error(f"Error determinando métodos aplicables: {str(e)}")
            return [], {"error": str(e)}

    def solve(self, model: MathematicalModel, method: str = "simplex") -> Dict[str, Any]:
        """
        Resuelve el modelo según el método elegido y devuelve resultados e intermedios.
        Métodos soportados: 'simplex', 'graphical', 'dual'
        """
        try:
            symbols = {name: sp.Symbol(name, real=True) for name in model.variables.keys()}
            objective = sp.sympify(model.objective_function, locals=symbols)
            constraints = model.constraints or []

            if method in ("simplex", "dual"):
                if pulp is None:
                    return {"success": False, "error": "PuLP no está instalado en el entorno"}

                prob_name = "LP_Problem"
                sense = pulp.LpMaximize if model.objective == "max" else pulp.LpMinimize
                prob = pulp.LpProblem(prob_name, sense)

                # Create pulp variables (non-negative)
                pv = {name: pulp.LpVariable(name, lowBound=0) for name in model.variables.keys()}

                # Objective: extract coefficients for each variable
                obj_expr = sp.expand(objective)
                coeffs = {}
                for name in model.variables.keys():
                    sym = symbols[name]
                    c = obj_expr.coeff(sym, 1)
                    coeffs[name] = float(c) if c is not None else 0.0

                prob += pulp.lpSum([coeffs[n] * pv[n] for n in pv])

                # Add constraints
                for c in constraints:
                    # try to parse relational
                    rel = sp.sympify(c, locals=symbols, evaluate=False)
                    if hasattr(rel, 'lhs') and hasattr(rel, 'rhs'):
                        lhs = rel.lhs
                        rhs = float(rel.rhs)
                        # Get linear expression coefficients
                        expr = sp.expand(lhs)
                        # Build pulp expression
                        terms = []
                        for name in pv.keys():
                            coeff = expr.coeff(symbols[name], 1)
                            coeff_val = float(coeff) if coeff is not None else 0.0
                            if abs(coeff_val) > 1e-12:
                                terms.append(coeff_val * pv[name])

                        if str(rel.rel_op) in ("<=", "LessThan") or "<=" in str(rel):
                            prob += pulp.lpSum(terms) <= rhs
                        elif str(rel.rel_op) in (">=", "GreaterThan") or ">=" in str(rel):
                            prob += pulp.lpSum(terms) >= rhs
                        elif str(rel.rel_op) in ("==", "Equality") or "=" in str(rel):
                            prob += pulp.lpSum(terms) == rhs
                        else:
                            # fallback: try substring
                            if "<=" in c:
                                prob += pulp.lpSum(terms) <= rhs
                            elif ">=" in c:
                                prob += pulp.lpSum(terms) >= rhs
                            elif "=" in c:
                                prob += pulp.lpSum(terms) == rhs
                    else:
                        # Try treating it as <= rhs
                        # skip invalid
                        continue

                # Solve
                solver = pulp.PULP_CBC_CMD(msg=False)
                result = prob.solve(solver)
                status = pulp.LpStatus.get(prob.status, str(prob.status))

                solution = {v.name: v.value() for v in prob.variables()}
                objective_value = pulp.value(prob.objective)

                # Intermediate info: standard form approximation
                intermed = {
                    "standard_form": {
                        "objective_coeffs": coeffs,
                        "constraints_count": len(constraints)
                    }
                }

                return {
                    "success": True,
                    "method": method,
                    "status": status,
                    "objective_value": objective_value,
                    "variables": solution,
                    "intermediate": intermed
                }

            elif method == "graphical":
                # Only for 1 or 2 variables
                var_names = list(model.variables.keys())
                if len(var_names) == 0:
                    return {"success": False, "error": "No hay variables definidas"}

                # Generate candidate corner points from intersections of constraint lines
                # Represent constraints as a*x + b*y (op) rhs
                parsed = []
                for c in constraints:
                    rel = sp.sympify(c, locals=symbols, evaluate=False)
                    if hasattr(rel, 'lhs') and hasattr(rel, 'rhs'):
                        parsed.append(rel)

                # build list of lines (as tuples of coefficients)
                def coeffs_of(expr):
                    expr_e = sp.expand(expr)
                    a = float(expr_e.coeff(symbols[var_names[0]], 1)) if var_names else 0.0
                    b = 0.0
                    if len(var_names) > 1:
                        b = float(expr_e.coeff(symbols[var_names[1]], 1))
                    return a, b

                points = set()
                # include origin
                points.add((0.0, 0.0))

                # intersections of each pair
                for i in range(len(parsed)):
                    for j in range(i+1, len(parsed)):
                        r1 = parsed[i]
                        r2 = parsed[j]
                        a1, b1 = coeffs_of(r1.lhs)
                        a2, b2 = coeffs_of(r2.lhs)
                        rhs1 = float(r1.rhs)
                        rhs2 = float(r2.rhs)
                        det = a1 * b2 - a2 * b1
                        if abs(det) < 1e-12:
                            continue
                        x = (rhs1 * b2 - rhs2 * b1) / det
                        y = (a1 * rhs2 - a2 * rhs1) / det
                        points.add((float(x), float(y)))

                # Evaluate feasible points and objective
                feasible = []
                best_point = None
                best_value = None
                for p in points:
                    x_val = {var_names[0]: p[0]} if len(var_names) >= 1 else {}
                    if len(var_names) >= 2:
                        x_val[var_names[1]] = p[1]
                    # check non-negativity
                    if any(v < -1e-9 for v in p):
                        continue
                    ok = True
                    for rel in parsed:
                        lhs = rel.lhs
                        rhs = float(rel.rhs)
                        # substitute
                        sub = lhs
                        for k, v in x_val.items():
                            sub = sub.subs(symbols[k], v)
                        val = float(sub)
                        op = str(rel.rel_op)
                        if "<=" in op or "LessThan" in op:
                            if val - rhs > 1e-6:
                                ok = False
                                break
                        elif ">=" in op or "GreaterThan" in op:
                            if rhs - val > 1e-6:
                                ok = False
                                break
                        elif "=" in op or "Equality" in op:
                            if abs(val - rhs) > 1e-6:
                                ok = False
                                break
                    if not ok:
                        continue
                    # compute objective
                    val = float(objective.subs({symbols.get(k): v for k, v in x_val.items()}))
                    feasible.append({"point": p, "objective": val})
                    if best_value is None or (model.objective == "max" and val > best_value) or (model.objective == "min" and val < best_value):
                        best_value = val
                        best_point = p

                return {
                    "success": True,
                    "method": "graphical",
                    "feasible_points": feasible,
                    "best_point": best_point,
                    "best_value": best_value
                }

            else:
                return {"success": False, "error": f"Método no soportado: {method}"}

        except Exception as e:
            logger.error(f"Error en SolverService.solve: {str(e)}")
            return {"success": False, "error": str(e)}

# Análisis de Sensibilidad Post-Óptimo

## Descripción General

El módulo de análisis de sensibilidad post-óptimo proporciona información detallada sobre cómo los cambios en los parámetros del problema de programación lineal afectan la solución óptima. Esta funcionalidad está disponible **únicamente** para los métodos:

- **Simplex** (maximización)
- **Simplex Dual** (minimización)
- **Gran M** (problemas con restricciones mixtas)

**Nota:** El método de Punto Interior y el método Gráfico **no** proporcionan análisis de sensibilidad debido a sus características algorítmicas.

## Componentes del Análisis

### 1. Rangos de Optimalidad (Coeficientes c_j)

Los rangos de optimalidad indican cuánto pueden variar los coeficientes de la función objetivo sin que cambie la **base óptima** (es decir, qué variables tienen valores positivos).

**Importante:** Aunque la base no cambie, el valor óptimo Z **sí cambiará** proporcionalmente dentro de estos rangos.

```json
{
  "variable": "x1",
  "current_value": 3.0,
  "lower_bound": 2.0,
  "upper_bound": 5.0,
  "allowable_decrease": 1.0,
  "allowable_increase": 2.0,
  "explanation": "...",
  "interpretation": "..."
}
```

### 2. Rangos de Factibilidad (RHS b_i)

Estos rangos indican cuánto pueden variar los términos independientes de las restricciones (lado derecho) mientras la misma base permanezca óptima.

**Importante:** Los precios sombra son válidos únicamente dentro de estos rangos.

### 3. Precios Sombra (Valores Duales π_i)

El precio sombra de una restricción representa el cambio en el valor óptimo por cada unidad de incremento en el lado derecho de la restricción.

**Interpretación económica:**
- Para **maximización**: El precio sombra indica cuánto aumentaría la ganancia si tuviéramos una unidad adicional del recurso.
- Para **minimización**: El precio sombra indica cuánto disminuiría el costo si relajáramos la restricción.

**Restricción activa (binding):** La restricción se cumple con igualdad exacta. Puede tener precio sombra ≠ 0.

**Restricción no activa:** Hay holgura (slack > 0). El precio sombra es 0.

```json
{
  "constraint_name": "Restricción 1",
  "value": 1.5,
  "binding": true,
  "slack_variable": "s1",
  "explanation": "...",
  "economic_interpretation": "..."
}
```

### 4. Costos Reducidos (c̄_j)

El costo reducido de una variable no básica indica cuánto debe mejorar su coeficiente en la función objetivo para que entre a la base.

- **Variables básicas:** Costo reducido = 0 (por definición)
- **Variables no básicas:** Indica el "costo de oportunidad" de incluir esa variable

## Uso de la API

### Endpoint: POST `/api/v1/analyze/solve`

```json
{
  "model": {
    "objective_function": "3*x1 + 2*x2",
    "constraints": ["2*x1 + x2 <= 18", "x1 >= 0", "x2 >= 0"],
    "variables": {"x1": "Producto 1", "x2": "Producto 2"},
    "objective": "max"
  },
  "method": "simplex"
}
```

### Respuesta con Análisis de Sensibilidad

```json
{
  "success": true,
  "result": {
    "objective_value": 27.0,
    "variables": {"x1": 9.0, "x2": 0.0},
    "sensitivity_analysis": {
      "objective_ranges": [...],
      "rhs_ranges": [...],
      "shadow_prices": [...],
      "reduced_costs": [...],
      "theory_explanation": "...",
      "practical_insights": [...]
    }
  }
}
```

## Teoría Matemática

### Rangos de Optimalidad para Variables Básicas

Para una variable básica $x_k$ en la fila $r$ del tableau óptimo:

Cuando $c_k$ cambia en $\Delta$, los costos reducidos cambian según:

$$\bar{c}_j' = \bar{c}_j - \Delta \cdot a_{rj}$$

El rango está determinado por mantener la condición de optimalidad:
- **Maximización:** $\bar{c}_j \leq 0$ para toda variable no básica
- **Minimización:** $\bar{c}_j \geq 0$ para toda variable no básica

### Rangos de Factibilidad

Para el término independiente $b_i$:

La solución básica actual es $\mathbf{x}_B = B^{-1}\mathbf{b}$

Al cambiar $b_i$ en $\Delta$:

$$\mathbf{x}_B' = \mathbf{x}_B + \Delta \cdot B^{-1}\mathbf{e}_i$$

El rango está determinado por: $\mathbf{x}_B' \geq 0$

### Precios Sombra

Los precios sombra son los coeficientes de las variables de holgura en la fila $Z$ del tableau óptimo:

$$\pi_i = c_B^T B^{-1} \mathbf{e}_i$$

Donde:
- $c_B$ es el vector de coeficientes de las variables básicas
- $B^{-1}$ es la inversa de la matriz de las columnas básicas
- $\mathbf{e}_i$ es el vector unitario

## Ejemplos Prácticos

### Ejemplo 1: Problema de Producción

```python
from app.schemas.analyze_schema import MathematicalModel
from app.services.solver_service import SolverService

model = MathematicalModel(
    objective_function="70*x1 + 120*x2",
    constraints=[
        "4*x1 + 6*x2 <= 120",  # Horas de trabajo
        "2*x1 + 3*x2 <= 72",   # Unidades de madera
        "x1 >= 0",
        "x2 >= 0"
    ],
    variables={
        "x1": "Sillas",
        "x2": "Mesas"
    },
    objective="max"
)

result = SolverService().solve(model, method="simplex")
sensitivity = result.get("sensitivity_analysis")

# Verificar precio sombra del trabajo
trabajo_sp = sensitivity["shadow_prices"][0]
print(f"Valor de una hora extra: ${trabajo_sp['value']}")
```

### Interpretación de Resultados

1. **Rangos de optimalidad:** Si la ganancia por silla aumenta de $70 a más de $80, podría cambiar la mezcla óptima de productos.

2. **Precios sombra:** Si el precio sombra del trabajo es $20, vale la pena pagar hasta $20 por hora extra de trabajo.

3. **Costos reducidos:** Si el costo reducido de las sillas es $10, la ganancia por silla debería aumentar en $10 para que sea rentable producirlas.

## Notas Técnicas

- Los rangos infinitos se representan como `null` en JSON y se formatean como "∞" o "-∞" en las cadenas de visualización.
- La tolerancia numérica utilizada es de $10^{-10}$ para comparaciones de igualdad.
- El análisis se realiza automáticamente al resolver el problema y se incluye en la respuesta.

## Referencias

- Taha, H. A. (2017). *Investigación de Operaciones*. Pearson Education.
- Hillier, F. S., & Lieberman, G. J. (2015). *Introduction to Operations Research*. McGraw-Hill.

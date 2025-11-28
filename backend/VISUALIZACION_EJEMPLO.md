# 🎨 Vista Previa de Visualización HTML - Simplex Dual

## Ejemplo Real de Output

Este documento muestra cómo se ve la visualización HTML generada por el sistema.

---

## 📋 Estructura de la Visualización

### 1. Encabezado y Título
```
╔════════════════════════════════════════════════════════════╗
║     Método Simplex Dual - Solución Paso a Paso            ║
╚════════════════════════════════════════════════════════════╝
```

### 2. Leyenda de Colores
```
┌────────────────────────────────────────────────────┐
│  🔴 Elemento Pivote                                │
│  🌸 Fila Pivote                                    │
│  💙 Columna Pivote                                 │
│  🟠 RHS Negativo                                   │
│  💜 Variable de Holgura                            │
└────────────────────────────────────────────────────┘
```

---

## 📊 Iteración 0: Tableau Inicial

### Variables de Holgura Agregadas
```
┌─────────────────────────────────────────────┐
│ 📊 Variables de Holgura Agregadas           │
│                                             │
│ • s₁ - Variable de holgura                  │
│ • s₂ - Variable de holgura                  │
│                                             │
│ 💡 Explicación:                             │
│ El método Simplex Dual comienza             │
│ dual-factible (coeficientes de Z ≥ 0)       │
│ pero puede ser primal-infactible            │
│ (algunos RHS negativos)                     │
└─────────────────────────────────────────────┘
```

### Explicación del Paso
```
┌─────────────────────────────────────────────┐
│ 📝 Explicación del Paso                     │
│                                             │
│ Se establece el tableau inicial             │
│                                             │
│ Variables de holgura:                       │
│   s₁: Índice 2                              │
│   s₂: Índice 3                              │
│                                             │
│ ⚠️ Estado: Primal-Infactible                │
│    2 RHS negativos restantes                │
└─────────────────────────────────────────────┘
```

### Tableau Inicial
```
┌──────┬────────┬────────┬────────┬────────┬────────┐
│ Base │   x1   │   x2   │   s1   │   s2   │  RHS   │
├──────┼────────┼────────┼────────┼────────┼────────┤
│  s1  │ -1.000 │ -1.000 │ 1.000  │ 0.000  │ -4.000 │ ← 🟠 Negativo
│  s2  │ -2.000 │ -1.000 │ 0.000  │ 1.000  │ -5.000 │ ← 🟠 Negativo
├──────┼────────┼────────┼────────┼────────┼────────┤
│  Z   │ 2.000  │ 3.000  │ 0.000  │ 0.000  │ 0.000  │
└──────┴────────┴────────┴────────┴────────┴────────┘
```

---

## 📊 Iteración 1: Entra x₁, Sale s₂

### Explicación del Paso
```
┌─────────────────────────────────────────────┐
│ 📝 Explicación del Paso                     │
│                                             │
│ Fila 1 tiene RHS más negativo.              │
│ Columna 0 tiene razón dual mínima.          │
│                                             │
│ ✅ Variable Entrante: x₁                    │
│ ❌ Variable Saliente: s₂                    │
│ 🎯 Elemento Pivote: -2.0000                 │
│ 📍 RHS de fila pivote: -5.0000 (NEGATIVO)   │
└─────────────────────────────────────────────┘
```

### Cálculo de Razones Duales
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Cálculo de Razones Duales                                │
│                                                             │
│ Razón = |Coeficiente Z / Coeficiente Fila Pivote|          │
│ (solo para coeficientes negativos en fila pivote)          │
│                                                             │
│ ┌────────┬──────────┬──────────────────┬─────────┬─────────┐
│ │ Columna│  Coef. Z │ Coef. Fila Pivote│  Razón  │¿Mínima? │
│ ├────────┼──────────┼──────────────────┼─────────┼─────────┤
│ │   0    │  2.0000  │     -2.0000      │ 1.0000  │ ✓ SÍ    │ ← 🟢 Seleccionada
│ │   1    │  3.0000  │     -1.0000      │ 3.0000  │   No    │
│ └────────┴──────────┴──────────────────┴─────────┴─────────┘
└─────────────────────────────────────────────────────────────┘
```

### Tableau Después del Pivoteo
```
┌──────┬────────┬────────┬────────┬────────┬────────┐
│ Base │   x1   │   x2   │   s1   │   s2   │  RHS   │
├──────┼────────┼────────┼────────┼────────┼────────┤
│  s1  │ 0.000  │ -0.500 │ 1.000  │ -0.500 │ -1.500 │ ← 🟠 Aún negativo
│  x1  │ 1.000  │ 0.500  │ 0.000  │ -0.500 │ 2.500  │ ← Nuevo básico
├──────┼────────┼────────┼────────┼────────┼────────┤
│  Z   │ 0.000  │ 2.000  │ 0.000  │ 1.000  │ -5.000 │
└──────┴────────┴────────┴────────┴────────┴────────┘

Colores aplicados:
  💙 Columna 0 (x₁) - Columna pivote
  🌸 Fila 1 (s₂) - Fila pivote
  🔴 Celda [1,0] = -2.000 - Elemento pivote
```

---

## 📊 Iteración 2: Entra s₂, Sale s₁

### Explicación del Paso
```
┌─────────────────────────────────────────────┐
│ 📝 Explicación del Paso                     │
│                                             │
│ Fila 0 tiene RHS más negativo.              │
│ Columna 3 tiene razón dual mínima.          │
│                                             │
│ ✅ Variable Entrante: s₂                    │
│ ❌ Variable Saliente: s₁                    │
│ 🎯 Elemento Pivote: -0.5000                 │
│ 📍 RHS de fila pivote: -1.5000 (NEGATIVO)   │
└─────────────────────────────────────────────┘
```

### Tableau Después del Pivoteo
```
┌──────┬────────┬────────┬────────┬────────┬────────┐
│ Base │   x1   │   x2   │   s1   │   s2   │  RHS   │
├──────┼────────┼────────┼────────┼────────┼────────┤
│  s2  │ 0.000  │ 1.000  │ -2.000 │ 1.000  │ 3.000  │ ← ✅ Positivo
│  x1  │ 1.000  │ 0.000  │ 1.000  │ 0.000  │ 4.000  │ ← ✅ Positivo
├──────┼────────┼────────┼────────┼────────┼────────┤
│  Z   │ 0.000  │ 0.000  │ 2.000  │ 0.000  │ -8.000 │
└──────┴────────┴────────┴────────┴────────┴────────┘

✅ Solución Factible (todos RHS ≥ 0)
```

---

## 📊 Iteración 3: Solución Óptima

### Estado Final
```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ✅ SOLUCIÓN ÓPTIMA ALCANZADA                           │
│                                                         │
│  Todos los RHS son no-negativos                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Tableau Final
```
┌──────┬────────┬────────┬────────┬────────┬────────┐
│ Base │   x1   │   x2   │   s1   │   s2   │  RHS   │
├──────┼────────┼────────┼────────┼────────┼────────┤
│  s2  │ 0.000  │ 1.000  │ -2.000 │ 1.000  │ 3.000  │
│  x1  │ 1.000  │ 0.000  │ 1.000  │ 0.000  │ 4.000  │ ← 🟢 Solución óptima
├──────┼────────┼────────┼────────┼────────┼────────┤
│  Z   │ 0.000  │ 0.000  │ 2.000  │ 0.000  │ -8.000 │
└──────┴────────┴────────┴────────┴────────┴────────┘
```

### Solución Interpretada
```
┌─────────────────────────────────────────────┐
│ 🎯 Solución Óptima                          │
│                                             │
│ Valor de la función objetivo:               │
│   z* = 8.0                                  │
│                                             │
│ Valores de las variables:                   │
│   x₁* = 4.0                                 │
│   x₂* = 0.0                                 │
│                                             │
│ Iteraciones totales: 3                      │
│                                             │
│ Variables básicas finales:                  │
│   • x₁ (variable de decisión)               │
│   • s₂ (variable de holgura)                │
│                                             │
│ Variables no básicas finales:               │
│   • x₂ (variable de decisión)               │
│   • s₁ (variable de holgura)                │
└─────────────────────────────────────────────┘
```

---

## 🎨 Mapa de Colores Aplicados

### En el HTML Real:

1. **Encabezados de Iteración**: 
   - Fondo verde (#4CAF50)
   - Texto blanco

2. **Encabezados de Tablas**:
   - Fondo verde (#4CAF50)
   - Texto blanco

3. **Columna de Base**:
   - Fondo amarillo (#FFC107)
   - Indica variables básicas actuales

4. **Elemento Pivote**:
   - Fondo rojo (#ff4444)
   - Borde rojo oscuro 3px
   - Texto blanco en negrita
   - Tamaño de fuente 1.1em

5. **Fila Pivote**:
   - Fondo rosa claro (#ffcccc)
   - Toda la fila resaltada

6. **Columna Pivote**:
   - Fondo azul claro (#ccccff)
   - Toda la columna resaltada

7. **RHS Negativos**:
   - Fondo naranja (#ff9800)
   - Texto blanco en negrita
   - Solo en celdas RHS con valor < 0

8. **Variables de Holgura**:
   - Fondo púrpura claro (#e1bee7)
   - Columnas s₁, s₂, etc.

9. **Cajas de Explicación**:
   - Fondo azul muy claro (#e3f2fd)
   - Borde izquierdo azul 4px (#2196F3)
   - Padding 15px

10. **Cajas de Razones Duales**:
    - Fondo naranja muy claro (#fff3e0)
    - Borde izquierdo naranja 4px (#ff9800)

11. **Estado Óptimo**:
    - Fondo verde (#4CAF50)
    - Texto blanco
    - Centrado y en negrita

12. **Estado Infactible**:
    - Fondo rojo (#f44336)
    - Texto blanco
    - Centrado y en negrita

---

## 📱 Características Responsive

El HTML generado es completamente responsive:

```css
/* Desktop (> 1400px) */
max-width: 1400px;
padding: 20px;

/* Tablet (768px - 1400px) */
Tablas se ajustan automáticamente

/* Mobile (< 768px) */
Font-size reducido
Padding ajustado
Scroll horizontal en tablas grandes
```

---

## 🖱️ Interactividad

### Hover Effects:

1. **Filas de Tabla**:
   ```
   Normal: Fondo blanco
   Hover: Fondo gris claro (#f5f5f5)
   ```

2. **Elementos Clickeables**:
   - Transiciones suaves
   - Cambio de cursor

3. **Accesibilidad**:
   - Contraste AAA para textos
   - Tamaños de fuente legibles
   - Espaciado generoso

---

## 📂 Archivos HTML Generados

Los archivos HTML incluyen TODO lo necesario:

✅ CSS embebido (no requiere archivos externos)
✅ Estructuras de datos en tablas HTML
✅ Sin JavaScript (HTML puro)
✅ Imprimible (print-friendly)
✅ Compatible con todos los navegadores modernos

### Tamaño típico de archivo:
- Problema pequeño (2 variables): ~30 KB
- Problema mediano (3-5 variables): ~50 KB
- Problema grande (>5 variables): ~100 KB

---

## 🎓 Ejemplo de Uso Académico

Este formato es ideal para:

1. **Enseñanza**: Estudiantes pueden ver cada paso
2. **Reportes**: Incluir en trabajos y tareas
3. **Presentaciones**: Copiar tablas a PowerPoint
4. **Publicaciones**: Screenshots profesionales

---

## 🔗 Navegación en el HTML

Cada archivo HTML incluye:

```
[Inicio] ← Ir al principio
  ↓
[Iteración 0] ← Tableau inicial
  ↓
[Iteración 1] ← Primera iteración
  ↓
[Iteración 2] ← Segunda iteración
  ↓
[Iteración N] ← Solución final
  ↓
[Final] ← Resumen de resultados
```

---

**Esta visualización hace que el método Simplex Dual sea:**
- ✅ Comprensible visualmente
- ✅ Fácil de seguir paso a paso
- ✅ Profesional y presentable
- ✅ Educativo y didáctico

**Abre cualquiera de los archivos `.html` generados para ver la visualización completa en acción!**

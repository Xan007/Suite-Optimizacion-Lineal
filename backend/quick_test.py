#!/usr/bin/env python
"""Test rápido del método gráfico - No ejecuta Django"""

import sys
import os

# Agregar path
sys.path.insert(0, os.path.dirname(__file__))

# Test imports
try:
    import matplotlib
    print("✓ matplotlib importado")
    
    import numpy as np
    print("✓ numpy importado")
    
    import sympy as sp
    print("✓ sympy importado")
    
    from app.services.graphication_service import GraphicationService
    print("✓ GraphicationService importado")
    
    from app.services.solver_service import SolverService
    print("✓ SolverService importado")
    
    print("\n✅ Todos los imports exitosos")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\nTodo está listo para usar el método gráfico.")

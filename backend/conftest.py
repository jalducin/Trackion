"""Configuración de pruebas: asegura que `app` y `vendor/` sean importables."""
import os
import sys

_ROOT = os.path.dirname(__file__)
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "vendor"))

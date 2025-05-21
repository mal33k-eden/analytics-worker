import importlib
import os
from pathlib import Path

models_dir = Path(__file__).parent
 
for file_path in models_dir.glob("*.py"):
    if file_path.name != "__init__.py":
        module_name = file_path.stem
        importlib.import_module(f"app.models.{module_name}")

print("Models loaded successfully")

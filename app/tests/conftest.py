import sys
from pathlib import Path

# Permite importar rag.py y main.py como en el contenedor (WORKDIR /codigo)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

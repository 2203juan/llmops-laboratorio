import shutil

import pytest

from src import RAIZ, cargar_config


def embedding_falso(texto):
    """Vector determinista para probar sin Ollama."""
    return [float(len(texto)), float(texto.count("a")), 1.0]


@pytest.fixture
def embedding():
    return embedding_falso


@pytest.fixture
def config(tmp_path):
    """Configuración real con todas las rutas dentro de una carpeta temporal."""
    shutil.copytree(RAIZ / "documentos", tmp_path / "documentos")
    return cargar_config(raiz=tmp_path)

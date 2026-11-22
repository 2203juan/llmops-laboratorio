"""Indexación del RAG por capas: extract (bronze), transform (silver y gold) y load (índice)."""

from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]


def cargar_config(ruta=None, raiz=RAIZ):
    """Lee config.yaml y convierte las rutas en absolutas respecto a `raiz`."""
    ruta = Path(ruta) if ruta else RAIZ / "config" / "config.yaml"
    config = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    config["rutas"] = {clave: Path(raiz) / valor for clave, valor in config["rutas"].items()}
    return config

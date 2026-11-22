"""Transform, silver -> gold (2 de 2): embeddings de los fragmentos con Ollama."""

import json
import os

import pandas as pd
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11435")


def crear_embedding(texto, modelo="nomic-embed-text", timeout=180):
    respuesta = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": modelo, "input": texto},
        timeout=timeout
    )
    respuesta.raise_for_status()
    return respuesta.json()["embeddings"][0]


def vectorizar_a_gold(config, embedding=None):
    """Guarda fragmentos y vectores en embeddings.json. Los tests reemplazan `embedding`."""
    gold, opciones = config["rutas"]["gold"], config["embedding"]
    embedding = embedding or (
        lambda texto: crear_embedding(texto, opciones["modelo"], opciones["timeout"])
    )
    fragmentos = pd.read_csv(gold / "fragmentos.csv", dtype={"texto": str}, keep_default_na=False)
    vectores = [
        {
            "fuente": f.fuente,
            "fragmento": int(f.fragmento),
            "texto": f.texto,
            "embedding": embedding(f.texto),
        }
        for f in fragmentos.itertuples()
    ]
    (gold / "embeddings.json").write_text(
        json.dumps(vectores, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return vectores

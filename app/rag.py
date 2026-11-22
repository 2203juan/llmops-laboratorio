import time

import mlflow
import numpy as np

from src import cargar_config
from src.load.load_indice import leer_indice
from src.transform.embeddings import crear_embedding

CONFIG = cargar_config()


# 1. Comparar vectores
def similitud_coseno(vector_a, vector_b):
    a = np.array(vector_a, dtype=float)
    b = np.array(vector_b, dtype=float)
    denominador = np.linalg.norm(a) * np.linalg.norm(b)
    if denominador == 0:
        return 0.0
    return float(np.dot(a, b) / denominador)


# 2. Recuperar los top_k fragmentos del índice que carga el pipeline
@mlflow.trace(name="recuperar_documentos")
def recuperar_documentos(pregunta, top_k=3):
    inicio = time.perf_counter()
    indice = leer_indice(CONFIG["rutas"]["indice"])
    if not indice:
        raise ValueError("El índice está vacío")
    vector_pregunta = crear_embedding(
        pregunta, CONFIG["embedding"]["modelo"], CONFIG["embedding"]["timeout"]
    )
    resultados = []
    for item in indice:
        resultados.append({
            "fuente": item["fuente"],
            "fragmento": item["fragmento"],
            "texto": item["texto"],
            "similitud": similitud_coseno(
                vector_pregunta, item["embedding"]
            )
        })
    resultados.sort(key=lambda x: x["similitud"], reverse=True)
    return {
        "fragmentos": resultados[:top_k],
        "tiempo_recuperacion": time.perf_counter() - inicio
    }

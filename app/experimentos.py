"""Experimentos A, B y C del tutorial: top_k, temperatura y preguntas sin evidencia.

Uso (desde la raíz del proyecto):
    python app/experimentos.py topk
    python app/experimentos.py temperatura
    python app/experimentos.py sin_evidencia
Guarda los resultados en datos/experimento_<nombre>.json.
"""

import json
import os
import sys
from pathlib import Path

import requests

API_URL = os.getenv("API_URL", "http://localhost:8020") + "/preguntar"
PREGUNTA_SEGURIDAD = "¿Qué debe hacer un operario si encuentra una condición insegura?"


def preguntar(pregunta, top_k=3, temperatura=0.2):
    respuesta = requests.post(
        API_URL,
        json={"pregunta": pregunta, "top_k": top_k, "temperatura": temperatura},
        timeout=360,
    )
    respuesta.raise_for_status()
    datos = respuesta.json()
    return {
        "pregunta": pregunta,
        "top_k": top_k,
        "temperatura": temperatura,
        "respuesta": datos["respuesta"].strip(),
        "tokens_entrada": datos["tokens_entrada"],
        "tokens_salida": datos["tokens_salida"],
        "tiempo_recuperacion": round(datos["tiempo_recuperacion"], 3),
        "duracion_ollama": round(datos["duracion_ollama"], 2),
        "similitud_maxima": round(max(f["similitud"] for f in datos["fuentes"]), 4),
        "fuentes": [f"{f['fuente']}#{f['fragmento']}" for f in datos["fuentes"]],
    }


def experimento_topk():
    return [preguntar(PREGUNTA_SEGURIDAD, top_k=k) for k in (1, 3, 5)]


def experimento_temperatura(repeticiones=3):
    return [
        preguntar("¿Cada cuánto se realiza mantenimiento preventivo?", temperatura=t)
        for t in (0, 0.5, 1)
        for _ in range(repeticiones)
    ]


def experimento_sin_evidencia():
    preguntas = [
        "¿Cuál es el salario del gerente?",
        "¿Cuál fue la facturación de TecnoFábrica el año pasado?",
        "¿Cuántos empleados tiene TecnoFábrica?",
    ]
    return [preguntar(p) for p in preguntas]


EXPERIMENTOS = {
    "topk": experimento_topk,
    "temperatura": experimento_temperatura,
    "sin_evidencia": experimento_sin_evidencia,
}

if __name__ == "__main__":
    nombre = sys.argv[1] if len(sys.argv) > 1 else ""
    if nombre not in EXPERIMENTOS:
        sys.exit(f"Uso: python app/experimentos.py {{{'|'.join(EXPERIMENTOS)}}}")
    resultados = EXPERIMENTOS[nombre]()
    salida = Path(f"datos/experimento_{nombre}.json")
    salida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in resultados:
        print(f"k={r['top_k']} t={r['temperatura']} | in={r['tokens_entrada']} out={r['tokens_salida']} "
              f"| sim={r['similitud_maxima']} | {r['duracion_ollama']}s | {r['respuesta'][:90]!r}")
    print(f"Guardado en {salida}")

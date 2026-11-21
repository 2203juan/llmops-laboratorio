"""Cliente de terminal para la API: indexar y preguntar (lo usa el Makefile)."""

import os
import sys

import requests

API = os.getenv("API_URL", "http://localhost:8020")


def indexar():
    datos = requests.post(f"{API}/indexar", timeout=600)
    datos.raise_for_status()
    d = datos.json()
    print(f"  ✓ {d['documentos']} documentos, {d['fragmentos']} fragmentos indexados")


def preguntar(pregunta, top_k=3, temperatura=0.2):
    r = requests.post(
        f"{API}/preguntar",
        json={"pregunta": pregunta, "top_k": int(top_k), "temperatura": float(temperatura)},
        timeout=360,
    )
    r.raise_for_status()
    d = r.json()
    print(f"\n  Pregunta:  {d['pregunta']}")
    print(f"  Respuesta: {d['respuesta'].strip()}\n")
    print(
        f"  tokens entrada={d['tokens_entrada']}  salida={d['tokens_salida']}  "
        f"ollama={d['duracion_ollama']:.2f}s  recuperación={d['tiempo_recuperacion']:.3f}s"
    )
    for f in d["fuentes"]:
        print(f"  fuente: {f['fuente']}#{f['fragmento']}  similitud={f['similitud']:.3f}")
    print()


if __name__ == "__main__":
    comando, *args = sys.argv[1:] or [""]
    if comando == "indexar":
        indexar()
    elif comando == "preguntar":
        preguntar(*args)
    else:
        sys.exit("Uso: python app/cliente.py indexar | preguntar <pregunta> [top_k] [temperatura]")

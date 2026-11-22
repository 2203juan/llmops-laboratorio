"""Load: carga gold en el índice SQLite que consulta la API."""

import json
import os
import sqlite3
from contextlib import closing

import pandas as pd


def cargar_indice(config):
    """Construye el índice en un archivo temporal y lo reemplaza al final.

    Así, si la carga falla, la API sigue consultando el índice anterior.
    """
    rutas = config["rutas"]
    destino = rutas["indice"]
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_name(destino.name + ".tmp")
    temporal.unlink(missing_ok=True)

    documentos = pd.read_csv(rutas["silver"] / "documentos.csv", dtype={"texto": str}, keep_default_na=False)
    fragmentos = pd.DataFrame(
        json.loads((rutas["gold"] / "embeddings.json").read_text(encoding="utf-8"))
    )
    fragmentos["embedding"] = fragmentos["embedding"].map(json.dumps)
    with closing(sqlite3.connect(temporal)) as conexion:
        documentos.to_sql("documentos", conexion, index=False)
        fragmentos.to_sql("fragmentos", conexion, index=False)
        conexion.commit()
    os.replace(temporal, destino)
    return {"documentos": len(documentos), "fragmentos": len(fragmentos)}


def leer_indice(ruta):
    """Devuelve los fragmentos con su embedding, en el orden en que se indexaron."""
    if not ruta.exists():
        raise FileNotFoundError("Primero debes indexar los documentos")
    with closing(sqlite3.connect(ruta)) as conexion:
        filas = conexion.execute(
            "SELECT fuente, fragmento, texto, embedding FROM fragmentos ORDER BY rowid"
        ).fetchall()
    return [
        {"fuente": f, "fragmento": n, "texto": t, "embedding": json.loads(e)}
        for f, n, t, e in filas
    ]

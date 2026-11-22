"""Transform, bronze -> silver: limpia los documentos."""

import unicodedata

import pandas as pd


def limpiar_texto(texto):
    """Normaliza Unicode, saltos de línea y espacios al final de línea; conserva el contenido."""
    texto = unicodedata.normalize("NFC", texto.lstrip("﻿"))
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    lineas = [linea.rstrip() for linea in texto.split("\n")]
    texto = "\n".join(lineas).strip("\n")
    return f"{texto}\n" if texto.strip() else ""


def limpiar_documentos(documentos):
    """Limpia los textos y descarta los documentos vacíos o repetidos."""
    tabla = pd.DataFrame(documentos, columns=["fuente", "texto"])
    tabla["texto"] = tabla["texto"].map(limpiar_texto)
    tabla = tabla[tabla["texto"] != ""].drop_duplicates(subset="texto")
    tabla = tabla.sort_values("fuente").reset_index(drop=True)
    tabla.insert(1, "titulo", tabla["texto"].map(lambda t: t.split("\n", 1)[0].strip()))
    tabla["n_caracteres"] = tabla["texto"].str.len()
    return tabla


def transformar_a_silver(config):
    bronze, silver = config["rutas"]["bronze"], config["rutas"]["silver"]
    silver.mkdir(parents=True, exist_ok=True)
    archivos = sorted(bronze.glob(config["patron_documentos"]))
    documentos = limpiar_documentos(
        [(a.name, a.read_text(encoding="utf-8")) for a in archivos]
    )
    if documentos.empty:
        raise ValueError("Ningún documento de bronze tiene contenido")
    documentos.to_csv(silver / "documentos.csv", index=False)
    return documentos

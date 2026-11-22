"""Transform, silver -> gold (1 de 2): divide los documentos en fragmentos con solape."""

import pandas as pd


def dividir_texto(texto, tamano=500, solape=80):
    if tamano <= solape:
        raise ValueError("El tamaño debe superar el solape")
    fragmentos = []
    inicio = 0
    while inicio < len(texto):
        fin = min(inicio + tamano, len(texto))
        fragmentos.append(texto[inicio:fin])
        if fin == len(texto):
            break
        inicio = fin - solape
    return fragmentos


def crear_fragmentos(documentos, tamano, solape):
    return pd.DataFrame([
        {"fuente": d.fuente, "fragmento": numero, "texto": texto, "n_caracteres": len(texto)}
        for d in documentos.itertuples()
        for numero, texto in enumerate(dividir_texto(d.texto, tamano, solape), start=1)
    ])


def fragmentar_a_gold(config):
    silver, gold = config["rutas"]["silver"], config["rutas"]["gold"]
    gold.mkdir(parents=True, exist_ok=True)
    documentos = pd.read_csv(silver / "documentos.csv", dtype={"texto": str}, keep_default_na=False)
    fragmentos = crear_fragmentos(documentos, **config["fragmentos"])
    fragmentos.to_csv(gold / "fragmentos.csv", index=False)
    return fragmentos

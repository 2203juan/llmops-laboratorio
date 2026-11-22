"""Calidad de cada capa, con los documentos reales y embeddings simulados (sin Ollama)."""

import json
import sqlite3
from contextlib import closing

import pandas as pd
import pytest

from main import ejecutar_pipeline
from src.load.load_indice import leer_indice


@pytest.fixture
def rutas(config, embedding):
    ejecutar_pipeline(config, embedding)
    return config["rutas"]


def test_silver_sin_nulos_ni_duplicados(rutas):
    documentos = pd.read_csv(rutas["silver"] / "documentos.csv")
    assert len(documentos) > 0
    assert not documentos.isna().any().any()
    assert documentos["fuente"].is_unique


def test_silver_conserva_todas_las_fuentes(rutas):
    documentos = pd.read_csv(rutas["silver"] / "documentos.csv")
    assert set(documentos["fuente"]) == {p.name for p in rutas["fuente"].glob("*.txt")}


def test_gold_respeta_el_tamano_y_un_solo_tamano_de_embedding(rutas, config):
    vectores = json.loads((rutas["gold"] / "embeddings.json").read_text(encoding="utf-8"))
    assert all(0 < len(i["texto"]) <= config["fragmentos"]["tamano"] for i in vectores)
    assert len({len(i["embedding"]) for i in vectores}) == 1


def test_indice_coincide_con_gold(rutas):
    vectores = json.loads((rutas["gold"] / "embeddings.json").read_text(encoding="utf-8"))
    assert leer_indice(rutas["indice"]) == vectores
    with closing(sqlite3.connect(rutas["indice"])) as conexion:
        tablas = {f[0] for f in conexion.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert tablas == {"documentos", "fragmentos"}


def test_pipeline_es_idempotente(rutas, config, embedding):
    antes = (rutas["gold"] / "embeddings.json").read_bytes()
    ejecutar_pipeline(config, embedding)
    assert (rutas["gold"] / "embeddings.json").read_bytes() == antes


def test_si_falla_el_embedding_se_conserva_el_indice_anterior(rutas, config):
    antes = leer_indice(rutas["indice"])

    def falla(_):
        raise RuntimeError("Ollama caído")

    with pytest.raises(RuntimeError):
        ejecutar_pipeline(config, falla)
    assert leer_indice(rutas["indice"]) == antes


def test_consultar_sin_indexar_falla(config):
    with pytest.raises(FileNotFoundError):
        leer_indice(config["rutas"]["indice"])

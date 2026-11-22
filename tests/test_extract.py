import hashlib

import pandas as pd
import pytest

from src.extract.extract_documentos import extraer_a_bronze


def test_bronze_es_copia_exacta_de_la_fuente(config):
    extraer_a_bronze(config)
    for original in config["rutas"]["fuente"].glob("*.txt"):
        copia = config["rutas"]["bronze"] / original.name
        assert copia.read_bytes() == original.read_bytes()


def test_manifiesto_registra_el_hash_de_cada_archivo(config):
    extraer_a_bronze(config)
    manifiesto = pd.read_csv(config["rutas"]["bronze"] / "manifiesto.csv")
    fuentes = sorted(p.name for p in config["rutas"]["fuente"].iterdir() if p.suffix == ".txt")
    assert sorted(manifiesto["archivo"]) == fuentes
    for fila in manifiesto.itertuples():
        contenido = (config["rutas"]["fuente"] / fila.archivo).read_bytes()
        assert fila.sha256 == hashlib.sha256(contenido).hexdigest()


def test_documento_retirado_de_la_fuente_sale_de_bronze(config):
    extraer_a_bronze(config)
    (config["rutas"]["fuente"] / "seguridad.txt").unlink()
    extraer_a_bronze(config)
    assert not (config["rutas"]["bronze"] / "seguridad.txt").exists()


def test_sin_documentos_falla(config):
    for archivo in config["rutas"]["fuente"].glob("*.txt"):
        archivo.unlink()
    with pytest.raises(FileNotFoundError):
        extraer_a_bronze(config)

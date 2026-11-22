"""Pipeline medallion: documentos -> bronze -> silver -> gold -> índice SQLite.

Uso: python main.py   (necesita Ollama con nomic-embed-text; ver OLLAMA_URL)
"""

import logging

from src import cargar_config
from src.extract.extract_documentos import extraer_a_bronze
from src.load.load_indice import cargar_indice
from src.transform.clean_documentos import transformar_a_silver
from src.transform.embeddings import vectorizar_a_gold
from src.transform.fragmentar import fragmentar_a_gold

logger = logging.getLogger("pipeline")


def configurar_logs(ruta):
    if logger.handlers:
        return
    ruta.parent.mkdir(parents=True, exist_ok=True)
    formato = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    for manejador in (logging.StreamHandler(), logging.FileHandler(ruta, encoding="utf-8")):
        manejador.setFormatter(formato)
        logger.addHandler(manejador)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def ejecutar_pipeline(config=None, embedding=None):
    config = config or cargar_config()
    configurar_logs(config["rutas"]["log"])
    try:
        manifiesto = extraer_a_bronze(config)
        logger.info("bronze: %d documentos copiados", len(manifiesto))
        documentos = transformar_a_silver(config)
        logger.info("silver: %d documentos limpios", len(documentos))
        fragmentos = fragmentar_a_gold(config)
        vectores = vectorizar_a_gold(config, embedding)
        logger.info("gold: %d fragmentos, %d embeddings", len(fragmentos), len(vectores))
        conteo = cargar_indice(config)
        logger.info("índice: %d documentos, %d fragmentos", conteo["documentos"], conteo["fragmentos"])
    except Exception:
        logger.exception("El pipeline falló")
        raise
    return conteo


if __name__ == "__main__":
    ejecutar_pipeline()

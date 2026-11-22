"""Extract: copia los documentos a bronze sin modificarlos."""

import hashlib
import shutil
from datetime import datetime, timezone

import pandas as pd


def extraer_a_bronze(config):
    """Copia los documentos byte a byte y registra su procedencia en manifiesto.csv."""
    origen, bronze = config["rutas"]["fuente"], config["rutas"]["bronze"]
    patron = config["patron_documentos"]
    documentos = sorted(origen.glob(patron))
    if not documentos:
        raise FileNotFoundError(f"No hay documentos en {origen}")
    bronze.mkdir(parents=True, exist_ok=True)

    # Un documento retirado de la fuente no debe seguir en bronze
    for anterior in bronze.glob(patron):
        anterior.unlink()

    fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifiesto = []
    for archivo in documentos:
        shutil.copyfile(archivo, bronze / archivo.name)
        contenido = (bronze / archivo.name).read_bytes()
        manifiesto.append({
            "archivo": archivo.name,
            "bytes": len(contenido),
            "sha256": hashlib.sha256(contenido).hexdigest(),
            "fecha_extraccion": fecha,
        })
    tabla = pd.DataFrame(manifiesto)
    tabla.to_csv(bronze / "manifiesto.csv", index=False)
    return tabla

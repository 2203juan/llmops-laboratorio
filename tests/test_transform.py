import pytest

from src.transform.clean_documentos import limpiar_documentos, limpiar_texto
from src.transform.fragmentar import crear_fragmentos, dividir_texto


def test_limpiar_texto_normaliza_sin_cambiar_el_contenido():
    assert limpiar_texto("﻿\r\nTítulo  \r\nlínea\t\r\n\r\n") == "Título\nlínea\n"
    assert limpiar_texto("política") == "política\n"
    assert limpiar_texto(" \n\t\n") == ""


def test_limpiar_documentos_descarta_vacios_y_repetidos():
    tabla = limpiar_documentos([("b.txt", "Uno\n"), ("a.txt", "Dos\n"), ("c.txt", "Uno\r\n"), ("d.txt", " \n")])
    assert list(tabla["fuente"]) == ["a.txt", "b.txt"]
    assert list(tabla["titulo"]) == ["Dos", "Uno"]


def test_texto_corto_queda_en_un_fragmento():
    assert dividir_texto("hola mundo", tamano=500, solape=80) == ["hola mundo"]


def test_fragmentos_se_solapan_y_cubren_todo_el_texto():
    texto = "".join(str(i % 10) for i in range(1200))
    fragmentos = dividir_texto(texto, tamano=500, solape=80)
    assert [len(f) for f in fragmentos] == [500, 500, 360]
    assert fragmentos[0][-80:] == fragmentos[1][:80]
    assert fragmentos[-1].endswith(texto[-50:])


def test_tamano_debe_superar_el_solape():
    with pytest.raises(ValueError):
        dividir_texto("abc", tamano=80, solape=80)


def test_gold_numera_los_fragmentos_por_documento():
    documentos = limpiar_documentos([("a.txt", "x" * 900), ("b.txt", "corto")])
    fragmentos = crear_fragmentos(documentos, tamano=500, solape=80)
    assert list(fragmentos["fuente"]) == ["a.txt", "a.txt", "b.txt"]
    assert list(fragmentos["fragmento"]) == [1, 2, 1]

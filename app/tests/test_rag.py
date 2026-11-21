import pytest

from rag import dividir_texto, similitud_coseno


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


def test_similitud_coseno():
    assert similitud_coseno([1, 0], [1, 0]) == pytest.approx(1.0)
    assert similitud_coseno([1, 0], [0, 1]) == pytest.approx(0.0)
    assert similitud_coseno([1, 2], [-1, -2]) == pytest.approx(-1.0)
    assert similitud_coseno([0, 0], [1, 1]) == 0.0

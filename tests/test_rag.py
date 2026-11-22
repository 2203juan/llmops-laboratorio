import pytest

from app.rag import similitud_coseno


def test_similitud_coseno():
    assert similitud_coseno([1, 0], [1, 0]) == pytest.approx(1.0)
    assert similitud_coseno([1, 0], [0, 1]) == pytest.approx(0.0)
    assert similitud_coseno([1, 2], [-1, -2]) == pytest.approx(-1.0)
    assert similitud_coseno([0, 0], [1, 1]) == 0.0

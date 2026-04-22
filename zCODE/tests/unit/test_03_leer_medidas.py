from pathlib import Path

import pytest


def test_limpiar_dax_remueve_prefijos_y_metadatos(m03):
    """Verify that DAX cleanup removes prefixes and TMDL metadata.

    Args:
        m03: Loaded module under test for measure reading.
    """
    # La limpieza debe eliminar signos igual iniciales y basura TMDL posterior.
    dax = "== SUM(Ventas[Monto]) changedProperty: x"

    assert m03.limpiar_dax(dax) == "SUM(Ventas[Monto])"


def test_leer_medidas_extrae_medida_dax(m03, pbix_root: Path):
    """Verify extraction of a multiline measure with normalized DAX.

    Args:
        m03: Loaded module under test for measure reading.
        pbix_root: Temporary PBIX root with Model/tables.
    """
    # La medida ocupa varias lineas y termina antes de formatString.
    tmdl = """table Ventas
measure Total Monto
    expression: = SUM ( Ventas[Monto]
    )
    formatString: #,0
"""
    (pbix_root / "Model" / "tables" / "Ventas.tmdl").write_text(tmdl, encoding="utf-8")

    resultado = m03.leer_medidas(str(pbix_root))

    # Se espera una sola medida con el DAX consolidado y limpio.
    assert len(resultado) == 1
    assert resultado[0]["tabla"] == "Ventas"
    assert resultado[0]["medida"] == "Total Monto"
    assert resultado[0]["dax"] == "SUM ( Ventas[Monto] )"


def test_leer_medidas_devuelve_vacio_sin_cierre_parentesis(m03, pbix_root: Path):
    """Verify that an unterminated expression does not produce a measure.

    Args:
        m03: Loaded module under test for measure reading.
        pbix_root: Temporary PBIX root with Model/tables.
    """
    # La heuristica actual solo confirma una medida cuando detecta cierre.
    tmdl = """table Ventas
measure SinCierre
    expression: = SUM(Ventas[Monto]
    formatString: #,0
"""
    (pbix_root / "Model" / "tables" / "Ventas.tmdl").write_text(tmdl, encoding="utf-8")

    assert m03.leer_medidas(str(pbix_root)) == []


def test_leer_medidas_lanza_si_no_existe_directorio(m03, tmp_path: Path):
    """Verify that a missing decomposed tree raises FileNotFoundError.

    Args:
        m03: Loaded module under test for measure reading.
        tmp_path: Temporary directory provided by pytest.
    """
    # La funcion no intenta adivinar rutas: falla con error claro.
    with pytest.raises(FileNotFoundError):
        m03.leer_medidas(str(tmp_path / "inexistente"))

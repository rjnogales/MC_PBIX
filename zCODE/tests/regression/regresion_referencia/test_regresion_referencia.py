from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest


# Esta suite detecta cambios no deseados comparando contra un baseline fijo (punto 4).
pytestmark = pytest.mark.regression


FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "regresion_referencia"
CASO_BASE_DIR = FIXTURES_DIR / "caso_base"
EXPECTED_FILE = FIXTURES_DIR / "expected_snapshot.json"


def _sorted_dict_rows(rows: list[dict], keys: list[str]) -> list[dict]:
    """Sort dictionary rows for deterministic snapshot comparison.

    Args:
        rows: Rows to sort.
        keys: Keys used to build the sort tuple.

    Returns:
        list[dict]: Sorted rows.
    """
    return sorted(rows, key=lambda r: tuple(r[k] for k in keys))


def _build_actual_snapshot(m01, m02, m03, m04) -> dict:
    """Build the current snapshot for the reference case.

    Args:
        m01: Loaded module under test for table reading.
        m02: Loaded module under test for column reading.
        m03: Loaded module under test for measure reading.
        m04: Loaded module under test for relationship reading.

    Returns:
        dict: Snapshot with counts and extracted metadata.
    """
    tablas = sorted(m01.leer_tablas(str(CASO_BASE_DIR)))
    columnas = _sorted_dict_rows(
        m02.leer_columnas(str(CASO_BASE_DIR)),
        ["tabla", "columna", "tipo"],
    )
    medidas = _sorted_dict_rows(
        m03.leer_medidas(str(CASO_BASE_DIR)),
        ["tabla", "medida", "dax"],
    )
    relaciones = _sorted_dict_rows(
        m04.leer_relaciones(str(CASO_BASE_DIR)),
        ["tabla_origen", "columna_origen", "tabla_destino", "columna_destino"],
    )

    return {
        "tablas": tablas,
        "conteos": {
            "tablas": len(tablas),
            "columnas": len(columnas),
            "medidas": len(medidas),
            "relaciones": len(relaciones),
        },
        "columnas": columnas,
        "medidas": medidas,
        "relaciones": relaciones,
    }


def test_snapshot_referencia_mantiene_resultado_esperado(m01, m02, m03, m04):
    """Verify that the current snapshot matches the expected reference.

    Args:
        m01: Loaded module under test for table reading.
        m02: Loaded module under test for column reading.
        m03: Loaded module under test for measure reading.
        m04: Loaded module under test for relationship reading.
    """
    expected = json.loads(EXPECTED_FILE.read_text(encoding="utf-8"))
    actual = _build_actual_snapshot(m01, m02, m03, m04)

    assert actual["conteos"] == expected["conteos"]
    assert actual["tablas"] == expected["tablas"]
    assert actual["columnas"] == expected["columnas"]
    assert actual["medidas"] == expected["medidas"]
    assert actual["relaciones"] == expected["relaciones"]


def test_excel_referencia_conserva_estructura(m01, m02, m03, m04, m05, tmp_path: Path):
    """Verify that the reference Excel keeps expected sheets and row counts.

    Args:
        m01: Loaded module under test for table reading.
        m02: Loaded module under test for column reading.
        m03: Loaded module under test for measure reading.
        m04: Loaded module under test for relationship reading.
        m05: Loaded module under test for Excel export.
        tmp_path: Temporary directory provided by pytest.
    """
    expected = json.loads(EXPECTED_FILE.read_text(encoding="utf-8"))

    tablas = pd.DataFrame({"tabla": m01.leer_tablas(str(CASO_BASE_DIR))})
    columnas = pd.DataFrame(m02.leer_columnas(str(CASO_BASE_DIR)))
    medidas = pd.DataFrame(m03.leer_medidas(str(CASO_BASE_DIR)))
    relaciones = pd.DataFrame(m04.leer_relaciones(str(CASO_BASE_DIR)))

    out = tmp_path / "referencia.xlsx"
    m05.exportar_excel(tablas, columnas, medidas, relaciones, out)

    xls = pd.ExcelFile(out)
    assert set(xls.sheet_names) == set(expected["excel"]["sheets"])

    for sheet, expected_rows in expected["excel"]["rows"].items():
        df = pd.read_excel(out, sheet_name=sheet)
        assert len(df) == expected_rows

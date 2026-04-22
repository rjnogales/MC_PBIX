from pathlib import Path

import pytest


def test_leer_columnas_extrae_tabla_columna_tipo(m02, pbix_root: Path):
    """Verify normalized extraction of table, column, and type.

    Args:
        m02: Loaded module under test for column reading.
        pbix_root: Temporary PBIX root with Model/tables.
    """
    # El fixture simula el formato minimo esperado en un .tmdl de tabla.
    tmdl = """table Ventas
column id
    dataType: int64
column descripcion
    dataType: string
"""
    (pbix_root / "Model" / "tables" / "Ventas.tmdl").write_text(tmdl, encoding="utf-8")

    resultado = m02.leer_columnas(str(pbix_root))

    # Cada columna debe salir normalizada con tabla, nombre y tipo.
    assert resultado == [
        {"tabla": "Ventas", "columna": "id", "tipo": "int64"},
        {"tabla": "Ventas", "columna": "descripcion", "tipo": "string"},
    ]


def test_leer_columnas_excluye_tecnicas(m02, pbix_root: Path):
    """Verify that technical tables do not contribute catalog columns.

    Args:
        m02: Loaded module under test for column reading.
        pbix_root: Temporary PBIX root with Model/tables.
    """
    # Aunque el contenido sea valido, las tablas tecnicas no se catalogan.
    tmdl = """table LocalDateTable
column fecha
    dataType: dateTime
"""
    (pbix_root / "Model" / "tables" / "LocalDateTable_1.tmdl").write_text(tmdl, encoding="utf-8")
    (pbix_root / "Model" / "tables" / "DateTableTemplate_1.tmdl").write_text(tmdl, encoding="utf-8")

    assert m02.leer_columnas(str(pbix_root)) == []


def test_leer_columnas_ignora_si_no_hay_data_type(m02, pbix_root: Path):
    """Verify that only columns with dataType are recorded.

    Args:
        m02: Loaded module under test for column reading.
        pbix_root: Temporary PBIX root with Model/tables.
    """
    # Solo se acepta una columna cuando aparece su dataType asociado.
    tmdl = """table Ventas
column id
column otro
    dataType: string
"""
    (pbix_root / "Model" / "tables" / "Ventas.tmdl").write_text(tmdl, encoding="utf-8")

    resultado = m02.leer_columnas(str(pbix_root))

    assert resultado == [{"tabla": "Ventas", "columna": "otro", "tipo": "string"}]


def test_leer_columnas_lanza_si_no_existe_directorio(m02, tmp_path: Path):
    """Verify that a missing base path raises FileNotFoundError.

    Args:
        m02: Loaded module under test for column reading.
        tmp_path: Temporary directory provided by pytest.
    """
    # La ausencia del arbol descompuesto se reporta como error de entrada.
    with pytest.raises(FileNotFoundError):
        m02.leer_columnas(str(tmp_path / "inexistente"))

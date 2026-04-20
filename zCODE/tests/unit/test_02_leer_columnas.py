from pathlib import Path

import pytest


def test_leer_columnas_extrae_tabla_columna_tipo(m02, pbix_root: Path):
    tmdl = """table Ventas
column id
    dataType: int64
column descripcion
    dataType: string
"""
    (pbix_root / "Model" / "tables" / "Ventas.tmdl").write_text(tmdl, encoding="utf-8")

    resultado = m02.leer_columnas(str(pbix_root))

    assert resultado == [
        {"tabla": "Ventas", "columna": "id", "tipo": "int64"},
        {"tabla": "Ventas", "columna": "descripcion", "tipo": "string"},
    ]


def test_leer_columnas_excluye_tecnicas(m02, pbix_root: Path):
    tmdl = """table LocalDateTable
column fecha
    dataType: dateTime
"""
    (pbix_root / "Model" / "tables" / "LocalDateTable_1.tmdl").write_text(tmdl, encoding="utf-8")
    (pbix_root / "Model" / "tables" / "DateTableTemplate_1.tmdl").write_text(tmdl, encoding="utf-8")

    assert m02.leer_columnas(str(pbix_root)) == []


def test_leer_columnas_ignora_si_no_hay_data_type(m02, pbix_root: Path):
    tmdl = """table Ventas
column id
column otro
    dataType: string
"""
    (pbix_root / "Model" / "tables" / "Ventas.tmdl").write_text(tmdl, encoding="utf-8")

    resultado = m02.leer_columnas(str(pbix_root))

    assert resultado == [{"tabla": "Ventas", "columna": "otro", "tipo": "string"}]


def test_leer_columnas_lanza_si_no_existe_directorio(m02, tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        m02.leer_columnas(str(tmp_path / "inexistente"))

from pathlib import Path

import pytest


def test_leer_tablas_excluye_tecnicas(m01, pbix_root: Path):
    """Verify that technical tables and non-TMDL files are excluded.

    Args:
        m01: Loaded module under test for table reading.
        pbix_root: Temporary PBIX root with Model/tables.
    """
    tables = pbix_root / "Model" / "tables"
    # Se mezclan tablas de negocio, tablas tecnicas y un archivo irrelevante.
    (tables / "Usos.tmdl").write_text("table Usos", encoding="utf-8")
    (tables / "DimRutas.tmdl").write_text("table DimRutas", encoding="utf-8")
    (tables / "LocalDateTable_123.tmdl").write_text("table LocalDateTable_123", encoding="utf-8")
    (tables / "DateTableTemplate_123.tmdl").write_text("table DateTableTemplate_123", encoding="utf-8")
    (tables / "README.txt").write_text("noop", encoding="utf-8")

    resultado = m01.leer_tablas(str(pbix_root))

    # Solo deben sobrevivir las tablas funcionales del modelo.
    assert set(resultado) == {"Usos", "DimRutas"}


def test_leer_tablas_lanza_si_no_existe_directorio(m01, tmp_path: Path):
    """Verify that a missing model path raises FileNotFoundError.

    Args:
        m01: Loaded module under test for table reading.
        tmp_path: Temporary directory provided by pytest.
    """
    # Sin estructura descompuesta, el extractor debe fallar explicitamente.
    with pytest.raises(FileNotFoundError):
        m01.leer_tablas(str(tmp_path / "inexistente"))


def test_leer_tablas_vacio(m01, pbix_root: Path):
    """Verify that a valid but empty directory returns an empty list.

    Args:
        m01: Loaded module under test for table reading.
        pbix_root: Temporary PBIX root with Model/tables.
    """
    # Un directorio valido pero sin .tmdl debe devolver lista vacia.
    assert m01.leer_tablas(str(pbix_root)) == []

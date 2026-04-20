from pathlib import Path

import pytest


def test_leer_tablas_excluye_tecnicas(m01, pbix_root: Path):
    tables = pbix_root / "Model" / "tables"
    (tables / "Usos.tmdl").write_text("table Usos", encoding="utf-8")
    (tables / "DimRutas.tmdl").write_text("table DimRutas", encoding="utf-8")
    (tables / "LocalDateTable_123.tmdl").write_text("table LocalDateTable_123", encoding="utf-8")
    (tables / "DateTableTemplate_123.tmdl").write_text("table DateTableTemplate_123", encoding="utf-8")
    (tables / "README.txt").write_text("noop", encoding="utf-8")

    resultado = m01.leer_tablas(str(pbix_root))

    assert set(resultado) == {"Usos", "DimRutas"}


def test_leer_tablas_lanza_si_no_existe_directorio(m01, tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        m01.leer_tablas(str(tmp_path / "inexistente"))


def test_leer_tablas_vacio(m01, pbix_root: Path):
    assert m01.leer_tablas(str(pbix_root)) == []

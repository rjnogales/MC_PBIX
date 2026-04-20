from pathlib import Path

import pytest


def test_leer_relaciones_parsea_referencias_con_comillas_y_brackets(m04, pbix_root: Path):
    rel = """relationship r1
    fromColumn: 'Tabla Uno'[Id]
    toColumn: DimRuta.IdRuta
"""
    (pbix_root / "Model" / "relationships.tmdl").write_text(rel, encoding="utf-8")

    resultado = m04.leer_relaciones(str(pbix_root))

    assert resultado == [
        {
            "tabla_origen": "Tabla Uno",
            "columna_origen": "Id",
            "tabla_destino": "DimRuta",
            "columna_destino": "IdRuta",
        }
    ]


def test_leer_relaciones_sin_punto_devuelve_columna_vacia(m04, pbix_root: Path):
    rel = """relationship r1
    fromColumn: SoloTabla
    toColumn: TablaDestino.ColumnaDestino
"""
    (pbix_root / "Model" / "relationships.tmdl").write_text(rel, encoding="utf-8")

    resultado = m04.leer_relaciones(str(pbix_root))

    assert resultado[0]["tabla_origen"] == "SoloTabla"
    assert resultado[0]["columna_origen"] == ""


def test_leer_relaciones_lanza_si_no_existe_archivo(m04, tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        m04.leer_relaciones(str(tmp_path / "inexistente"))

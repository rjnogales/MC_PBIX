from pathlib import Path

import pandas as pd
import pytest


# Esta suite valida reglas funcionales de negocio (punto 2), no cobertura tecnica.
pytestmark = pytest.mark.functional


def test_relaciones_negocio_apuntan_a_tablas_existentes(m01, m04, pbix_root: Path):
    """Verify that non-technical relationships point to existing tables.

    Args:
        m01: Loaded module under test for table reading.
        m04: Loaded module under test for relationship reading.
        pbix_root: Temporary PBIX root with decomposed metadata.
    """
    tables_dir = pbix_root / "Model" / "tables"
    (tables_dir / "Usos.tmdl").write_text("table Usos", encoding="utf-8")
    (tables_dir / "Rutas.tmdl").write_text("table Rutas", encoding="utf-8")

    rel = """relationship r1
    fromColumn: Usos.RUTA
    toColumn: Rutas.RUTA
relationship r2
    fromColumn: Usos.fecha
    toColumn: LocalDateTable_1.Date
"""
    (pbix_root / "Model" / "relationships.tmdl").write_text(rel, encoding="utf-8")

    tablas = set(m01.leer_tablas(str(pbix_root)))
    relaciones = m04.leer_relaciones(str(pbix_root))

    for r in relaciones:
        # Las relaciones tecnicas (LocalDateTable) se excluyen de esta regla.
        es_tecnica = "LocalDateTable" in r["tabla_origen"] or "LocalDateTable" in r["tabla_destino"]
        if not es_tecnica:
            assert r["tabla_origen"] in tablas
            assert r["tabla_destino"] in tablas


def test_medidas_tienen_dax_no_vacio(m03, pbix_root: Path):
    """Verify that each detected measure keeps a non-empty, clean DAX.

    Args:
        m03: Loaded module under test for measure reading.
        pbix_root: Temporary PBIX root with Model/tables.
    """
    tmdl = """table Usos
measure UsosProm
    expression: = SUM(Usos[USOSPAGOS])
    )
"""
    (pbix_root / "Model" / "tables" / "Usos.tmdl").write_text(tmdl, encoding="utf-8")

    medidas = m03.leer_medidas(str(pbix_root))

    assert len(medidas) == 1
    assert medidas[0]["dax"].strip() != ""
    assert not medidas[0]["dax"].lstrip().startswith("=")


def test_tabla_hecho_tiene_columna_numerica(m02, m05, pbix_root: Path):
    """Verify that each HECHO table has at least one numeric column.

    Args:
        m02: Loaded module under test for column reading.
        m05: Loaded module under test for classification/export.
        pbix_root: Temporary PBIX root with Model/tables.
    """
    (pbix_root / "Model" / "tables" / "Usos.tmdl").write_text(
        """table Usos
column RUTA
    dataType: string
column USOSPAGOS
    dataType: int64
""",
        encoding="utf-8",
    )
    (pbix_root / "Model" / "tables" / "Rutas.tmdl").write_text(
        """table Rutas
column RUTA
    dataType: string
""",
        encoding="utf-8",
    )

    columnas = pd.DataFrame(m02.leer_columnas(str(pbix_root)))
    tablas = pd.DataFrame({"tabla": sorted(columnas["tabla"].unique())})
    tablas = m05.clasificar_tablas(tablas)

    tipos_numericos = {"int64", "double", "decimal", "wholeNumber"}

    for tabla in tablas.loc[tablas["tipo"] == "HECHO", "tabla"]:
        cols_tabla = columnas.loc[columnas["tabla"] == tabla, "tipo"].str.lower().tolist()
        assert any(t in tipos_numericos for t in cols_tabla)


def test_export_excel_mantiene_consistencia_de_tablas(m05, tmp_path: Path):
    """Verify that exported Excel does not reference tables outside the catalog.

    Args:
        m05: Loaded module under test for classification/export.
        tmp_path: Temporary directory provided by pytest.
    """
    tablas = pd.DataFrame({"tabla": ["Usos", "Rutas"]})
    columnas = pd.DataFrame(
        [
            {"tabla": "Usos", "columna": "RUTA", "tipo": "string"},
            {"tabla": "Usos", "columna": "USOSPAGOS", "tipo": "int64"},
            {"tabla": "Rutas", "columna": "RUTA", "tipo": "string"},
        ]
    )
    medidas = pd.DataFrame([{"tabla": "Usos", "medida": "Total", "dax": "SUM(Usos[USOSPAGOS])"}])
    relaciones = pd.DataFrame(
        [
            {
                "tabla_origen": "Usos",
                "columna_origen": "RUTA",
                "tabla_destino": "Rutas",
                "columna_destino": "RUTA",
            }
        ]
    )

    out = tmp_path / "funcional.xlsx"
    m05.exportar_excel(tablas, columnas, medidas, relaciones, out)

    df_tablas = pd.read_excel(out, sheet_name="Tablas")
    df_columnas = pd.read_excel(out, sheet_name="Columnas")
    df_relaciones = pd.read_excel(out, sheet_name="Relaciones")

    set_tablas = set(df_tablas["tabla"].tolist())

    assert set(df_columnas["tabla"].tolist()).issubset(set_tablas)
    assert set(df_relaciones["tabla_origen"].tolist()).issubset(set_tablas)
    assert set(df_relaciones["tabla_destino"].tolist()).issubset(set_tablas)

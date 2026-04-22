from pathlib import Path

import pandas as pd


def test_clasificar_tabla_nombre(m05):
    """Verify heuristic classification based on table name.

    Args:
        m05: Loaded module under test for Excel export.
    """
    # La heuristica distingue hechos, dimensiones y casos no reconocidos.
    assert m05.clasificar_tabla_nombre("Usos Operativos") == "HECHO"
    assert m05.clasificar_tabla_nombre("TablaCalendario") == "DIMENSION"
    assert m05.clasificar_tabla_nombre("CatalogoGeneral") == "OTRO"


def test_clasificar_tablas_y_columnas(m05):
    """Verify that table classification propagates to related columns.

    Args:
        m05: Loaded module under test for Excel export.
    """
    # El tipo calculado para la tabla debe propagarse luego a sus columnas.
    tablas = pd.DataFrame({"tabla": ["Usos", "TablaCalendario", "Inventario"]})
    columnas = pd.DataFrame(
        {
            "tabla": ["Usos", "Inventario"],
            "columna": ["id", "nombre"],
            "tipo": ["int64", "string"],
        }
    )

    tablas_clas = m05.clasificar_tablas(tablas)
    columnas_clas = m05.clasificar_columnas(columnas, tablas_clas)

    assert list(tablas_clas["tipo"]) == ["HECHO", "DIMENSION", "OTRO"]
    assert list(columnas_clas["tipo_tabla"]) == ["HECHO", "OTRO"]


def test_clasificar_relaciones_y_glosario(m05):
    """Verify relationship classification and base glossary structure.

    Args:
        m05: Loaded module under test for Excel export.
    """
    # Se prueba una relacion de negocio y otra tecnica contra LocalDateTable.
    relaciones = pd.DataFrame(
        [
            {
                "tabla_origen": "Usos",
                "columna_origen": "id",
                "tabla_destino": "Rutas",
                "columna_destino": "id",
            },
            {
                "tabla_origen": "Usos",
                "columna_origen": "fecha",
                "tabla_destino": "LocalDateTable_1",
                "columna_destino": "Date",
            },
        ]
    )

    rel_clas = m05.clasificar_relaciones(relaciones)
    glosario = m05.crear_glosario()

    # El glosario debe conservar la estructura base del archivo Excel.
    assert list(rel_clas["tipo_relacion"]) == ["negocio", "tecnica"]
    assert list(glosario.columns) == ["Elemento", "Detalle"]
    assert len(glosario) >= 10


def test_exportar_excel_genera_archivo_y_hojas(m05, tmp_path: Path):
    """Verify that export creates a workbook with the expected sheets.

    Args:
        m05: Loaded module under test for Excel export.
        tmp_path: Temporary directory provided by pytest.
    """
    # Se arma un caso minimo de punta a punta para verificar el libro generado.
    tablas = pd.DataFrame({"tabla": ["Usos", "Rutas"]})
    columnas = pd.DataFrame(
        [
            {"tabla": "Usos", "columna": "id", "tipo": "int64"},
            {"tabla": "Rutas", "columna": "codigo", "tipo": "string"},
        ]
    )
    medidas = pd.DataFrame([{"tabla": "Usos", "medida": "Total", "dax": "SUM(Usos[id])"}])
    relaciones = pd.DataFrame(
        [
            {
                "tabla_origen": "Usos",
                "columna_origen": "id",
                "tabla_destino": "Rutas",
                "columna_destino": "id",
            }
        ]
    )

    salida = tmp_path / "diccionario.xlsx"
    m05.exportar_excel(tablas, columnas, medidas, relaciones, salida)

    assert salida.exists()

    excel = pd.ExcelFile(salida)
    assert set(excel.sheet_names) == {"Tablas", "Columnas", "Medidas", "Relaciones", "Glosario"}

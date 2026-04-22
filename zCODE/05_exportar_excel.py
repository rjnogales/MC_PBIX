"""Clasificacion de metadatos y exportacion a Excel por PBIX."""

import pandas as pd

# =========================
# CLASIFICACIÓN TABLAS
# =========================
CLASIFICACION_TABLAS = {
    "Usos": "HECHO",
    "UsosGPS": "HECHO",
    "01 UsosEMV": "HECHO",
    "Flota Dia": "HECHO",
    "Flota Ruta": "HECHO",
    "01 FlotaTipologiaCOT": "HECHO",
    "Kilometros Ruta": "HECHO",
    "Kilometros Dia": "HECHO",
    "01 kmsEjecutadosCOTTipologia": "HECHO",
    "01 KmsPSOTipologia_Cot": "HECHO",
    "Puntualidad": "HECHO",
    "01 IETipologiaCOT": "HECHO",

    "TablaCalendario": "DIMENSION",
    "Rutas": "DIMENSION",
    "Tipologia": "DIMENSION",
    "Concesionarios": "DIMENSION",
    "Estaciones": "DIMENSION",
    "ACTCDE": "DIMENSION",
}


def clasificar_tabla_nombre(nombre):
    """Classify a table by name heuristics.

    Args:
        nombre: Table name to classify.

    Returns:
        str: Table type label such as HECHO, DIMENSION, or OTRO.
    """
    nombre = nombre.lower()

    # Estas palabras clave apuntan a tablas transaccionales o de metricas.
    if any(p in nombre for p in ["uso", "flota", "km", "kilometro", "puntualidad", "ie"]):
        return "HECHO"

    # Estas palabras clave suelen describir dimensiones de analisis.
    if any(p in nombre for p in ["ruta", "calendario", "fecha", "tipologia", "concesionario", "estacion"]):
        return "DIMENSION"

    return "OTRO"


def clasificar_tablas(df_tablas):
    """Add the analytical type column to the tables DataFrame.

    Args:
        df_tablas: DataFrame with at least the tabla column.

    Returns:
        pd.DataFrame: Same DataFrame enriched with the tipo column.
    """
    def clasificar(tabla):
        """Resolve the classification for a single table name.

        Args:
            tabla: Table name to classify.

        Returns:
            str: Analytical table type.
        """
        # Primero se respeta el catalogo manual; si no existe, aplica heuristica.
        if tabla in CLASIFICACION_TABLAS:
            return CLASIFICACION_TABLAS[tabla]
        return clasificar_tabla_nombre(tabla)

    df_tablas["tipo"] = df_tablas["tabla"].apply(clasificar)
    return df_tablas


def clasificar_columnas(df_columnas, df_tablas):
    """Propagate table classification into the columns DataFrame.

    Args:
        df_columnas: DataFrame with column metadata.
        df_tablas: DataFrame with classified tables.

    Returns:
        pd.DataFrame: Columns DataFrame enriched with table type information.
    """
    df_columnas = df_columnas.merge(
        df_tablas[["tabla", "tipo"]],
        on="tabla",
        how="left",
        suffixes=("", "_tabla")
    )
    if "tipo_tabla" not in df_columnas.columns and "tipo" in df_columnas.columns:
        # Solo ocurre cuando el dataframe de columnas no trae su propio campo "tipo".
        df_columnas = df_columnas.rename(columns={"tipo": "tipo_tabla"})
    return df_columnas


def clasificar_relaciones(df_relaciones):
    """Classify relationships as business or technical.

    Args:
        df_relaciones: DataFrame with relationship metadata.

    Returns:
        pd.DataFrame: Relationships DataFrame enriched with tipo_relacion.
    """
    def tipo_relacion(row):
        """Resolve the relationship type for one row.

        Args:
            row: Relationship row from the DataFrame.

        Returns:
            str: Relationship type label.
        """
        # Las relaciones con tablas tecnicas de calendario no se consideran de negocio.
        if "LocalDateTable" in row["tabla_destino"] or "LocalDateTable" in row["tabla_origen"]:
            return "tecnica"
        return "negocio"

    df_relaciones["tipo_relacion"] = df_relaciones.apply(tipo_relacion, axis=1)
    return df_relaciones


def crear_glosario():
    """Build the glossary sheet used in the output workbook.

    Returns:
        pd.DataFrame: Glossary content for the Excel output.
    """
    data = [
        ["HOJA", "DESCRIPCIÓN"],
        ["TABLAS", "Listado de tablas del modelo analítico."],
        ["COLUMNAS", "Columnas por tabla."],
        ["MEDIDAS", "Medidas DAX."],
        ["RELACIONES", "Relaciones entre tablas."],
        ["", ""],
        ["CAMPO", "DESCRIPCIÓN"],
        ["tipo", "HECHO, DIMENSION u OTRO"],
        ["HECHO", "Tabla principal de métricas o eventos (ej. usos, flota, kilómetros, puntualidad)."],
        ["DIMENSION", "Tabla de contexto para análisis (ej. fecha, ruta, tipología, concesionario, estación)."],
        ["OTRO", "Tabla que no coincide con reglas de HECHO o DIMENSION."],
        ["tipo_relacion", "negocio o tecnica"],
        ["", ""],
        ["NOTA", "Documento generado automáticamente."]
    ]

    return pd.DataFrame(data, columns=["Elemento", "Detalle"])


def exportar_excel(tablas, columnas, medidas, relaciones, output_file):
    """Export tables, columns, measures, relationships, and glossary to Excel.

    Args:
        tablas: DataFrame with table metadata.
        columnas: DataFrame with column metadata.
        medidas: DataFrame with measure metadata.
        relaciones: DataFrame with relationship metadata.
        output_file: Output workbook path.
    """

    # La exportacion deja el archivo ya enriquecido con clasificacion analitica.
    tablas = clasificar_tablas(tablas)
    columnas = clasificar_columnas(columnas, tablas)
    relaciones = clasificar_relaciones(relaciones)

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        # Cada hoja corresponde a una vista util para catalogo y auditoria.

        tablas.to_excel(writer, sheet_name='Tablas', index=False)
        columnas.to_excel(writer, sheet_name='Columnas', index=False)
        medidas.to_excel(writer, sheet_name='Medidas', index=False)
        relaciones.to_excel(writer, sheet_name='Relaciones', index=False)

        glosario = crear_glosario()
        glosario.to_excel(writer, sheet_name='Glosario', index=False)

        
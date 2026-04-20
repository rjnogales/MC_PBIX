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
    """Clasifica una tabla por heuristica de nombre."""
    nombre = nombre.lower()

    if any(p in nombre for p in ["uso", "flota", "km", "kilometro", "puntualidad", "ie"]):
        return "HECHO"

    if any(p in nombre for p in ["ruta", "calendario", "fecha", "tipologia", "concesionario", "estacion"]):
        return "DIMENSION"

    return "OTRO"


def clasificar_tablas(df_tablas):
    """Agrega la columna tipo (HECHO, DIMENSION u OTRO) al dataframe de tablas."""
    def clasificar(tabla):
        if tabla in CLASIFICACION_TABLAS:
            return CLASIFICACION_TABLAS[tabla]
        return clasificar_tabla_nombre(tabla)

    df_tablas["tipo"] = df_tablas["tabla"].apply(clasificar)
    return df_tablas


def clasificar_columnas(df_columnas, df_tablas):
    """Propaga el tipo de tabla al dataframe de columnas."""
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
    """Clasifica relaciones como negocio o tecnica."""
    def tipo_relacion(row):
        if "LocalDateTable" in row["tabla_destino"] or "LocalDateTable" in row["tabla_origen"]:
            return "tecnica"
        return "negocio"

    df_relaciones["tipo_relacion"] = df_relaciones.apply(tipo_relacion, axis=1)
    return df_relaciones


def crear_glosario():
    """Construye la hoja de glosario para el Excel de salida."""
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
    """
    Exporta tablas, columnas, medidas, relaciones y glosario a un solo archivo Excel.

    Parametros:
        tablas (pd.DataFrame): Dataframe de tablas.
        columnas (pd.DataFrame): Dataframe de columnas.
        medidas (pd.DataFrame): Dataframe de medidas.
        relaciones (pd.DataFrame): Dataframe de relaciones.
        output_file (Path | str): Ruta del archivo de salida.
    """

    # Clasificación (se hace aquí porque es parte del modelo analítico)
    tablas = clasificar_tablas(tablas)
    columnas = clasificar_columnas(columnas, tablas)
    relaciones = clasificar_relaciones(relaciones)

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:

        tablas.to_excel(writer, sheet_name='Tablas', index=False)
        columnas.to_excel(writer, sheet_name='Columnas', index=False)
        medidas.to_excel(writer, sheet_name='Medidas', index=False)
        relaciones.to_excel(writer, sheet_name='Relaciones', index=False)

        glosario = crear_glosario()
        glosario.to_excel(writer, sheet_name='Glosario', index=False)

        
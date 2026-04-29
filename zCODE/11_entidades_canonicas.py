"""Construye entidades canonicas desde el diccionario normalizado."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import re

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

AREA_ID_MANUAL = ""
AREA_ID_DEFAULT = "OFICINA_EVALUACION"
AREA_ID = (
    AREA_ID_MANUAL.strip()
    or os.getenv("PBIX_AREA", AREA_ID_DEFAULT).strip()
    or AREA_ID_DEFAULT
)

AREA_DIR = PROJECT_DIR / AREA_ID
OUTPUT_DIR = AREA_DIR / "PBIXs_output"
NORMALIZADO_DIR = OUTPUT_DIR / "normalizado"
SILVER_DIR = OUTPUT_DIR / "silver"
ENTIDADES_DIR = SILVER_DIR / "entidades"


def log(mensaje: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {mensaje}")


def encontrar_ultimo_normalizado() -> Path | None:
    if not NORMALIZADO_DIR.exists():
        return None

    candidatos = sorted(NORMALIZADO_DIR.glob("Diccionario_Normalizado_*.xlsx"))
    if not candidatos:
        return None

    return max(candidatos, key=lambda p: p.stat().st_mtime)


def tipo_entidad(tipo_tabla: str | None) -> str:
    if not tipo_tabla:
        return "desconocida"

    valor = str(tipo_tabla).strip().lower()
    if "hecho" in valor:
        return "fact"
    if "dimension" in valor:
        return "dimension"
    return "referencia"


def es_clave_candidata(nombre_columna: str | None) -> bool:
    if not nombre_columna:
        return False

    nombre = str(nombre_columna).strip().lower()
    patrones = [
        r"^id$",
        r"^id_",
        r"_id$",
        r"^codigo$",
        r"^codigo_",
        r"_codigo$",
        r"^clave$",
        r"^clave_",
        r"_clave$",
    ]
    return any(re.search(patron, nombre) for patron in patrones)


def construir_entidades(df_tablas: pd.DataFrame) -> pd.DataFrame:
    entidades = df_tablas.copy()

    columnas_requeridas = ["tabla", "tabla_canon", "tipo_canon", "pbix_source"]
    for c in columnas_requeridas:
        if c not in entidades.columns:
            entidades[c] = None

    entidades = entidades[columnas_requeridas].drop_duplicates().reset_index(drop=True)
    entidades["entidad"] = entidades["tabla_canon"].fillna(entidades["tabla"])
    entidades["entidad_tipo"] = entidades["tipo_canon"].apply(tipo_entidad)

    return entidades[["entidad", "entidad_tipo", "tabla", "tabla_canon", "tipo_canon", "pbix_source"]]


def construir_atributos(df_columnas: pd.DataFrame) -> pd.DataFrame:
    columnas = df_columnas.copy()

    columnas_requeridas = [
        "tabla",
        "tabla_canon",
        "columna",
        "columna_canon",
        "tipo",
        "tipo_dato_canon",
        "pbix_source",
    ]
    for c in columnas_requeridas:
        if c not in columnas.columns:
            columnas[c] = None

    atributos = columnas[columnas_requeridas].drop_duplicates().reset_index(drop=True)
    atributos["entidad"] = atributos["tabla_canon"].fillna(atributos["tabla"])
    atributos["atributo"] = atributos["columna_canon"].fillna(atributos["columna"])
    atributos["es_clave_candidata"] = atributos["atributo"].apply(es_clave_candidata)

    return atributos[
        [
            "entidad",
            "atributo",
            "tipo_dato_canon",
            "tipo",
            "es_clave_candidata",
            "tabla",
            "columna",
            "tabla_canon",
            "columna_canon",
            "pbix_source",
        ]
    ]


def construir_relaciones(df_relaciones: pd.DataFrame) -> pd.DataFrame:
    relaciones = df_relaciones.copy()

    columnas_requeridas = [
        "tabla_origen",
        "tabla_destino",
        "columna_origen",
        "columna_destino",
        "tabla_origen_canon",
        "tabla_destino_canon",
        "columna_origen_canon",
        "columna_destino_canon",
        "tipo_relacion",
        "tipo_relacion_canon",
        "pbix_source",
    ]
    for c in columnas_requeridas:
        if c not in relaciones.columns:
            relaciones[c] = None

    relaciones = relaciones[columnas_requeridas].drop_duplicates().reset_index(drop=True)
    relaciones["entidad_origen"] = relaciones["tabla_origen_canon"].fillna(relaciones["tabla_origen"])
    relaciones["entidad_destino"] = relaciones["tabla_destino_canon"].fillna(relaciones["tabla_destino"])
    relaciones["atributo_origen"] = relaciones["columna_origen_canon"].fillna(relaciones["columna_origen"])
    relaciones["atributo_destino"] = relaciones["columna_destino_canon"].fillna(relaciones["columna_destino"])

    return relaciones[
        [
            "entidad_origen",
            "atributo_origen",
            "entidad_destino",
            "atributo_destino",
            "tipo_relacion_canon",
            "tipo_relacion",
            "tabla_origen",
            "columna_origen",
            "tabla_destino",
            "columna_destino",
            "pbix_source",
        ]
    ]


def construir_resumen(entidades: pd.DataFrame, atributos: pd.DataFrame, relaciones: pd.DataFrame) -> pd.DataFrame:
    resumen = [
        {"metrica": "entidades", "valor": int(len(entidades))},
        {"metrica": "atributos", "valor": int(len(atributos))},
        {"metrica": "relaciones", "valor": int(len(relaciones))},
        {
            "metrica": "entidades_fact",
            "valor": int((entidades["entidad_tipo"] == "fact").sum()) if "entidad_tipo" in entidades else 0,
        },
        {
            "metrica": "entidades_dimension",
            "valor": int((entidades["entidad_tipo"] == "dimension").sum()) if "entidad_tipo" in entidades else 0,
        },
    ]
    return pd.DataFrame(resumen)


def exportar_salida(
    entidades: pd.DataFrame,
    atributos: pd.DataFrame,
    relaciones: pd.DataFrame,
    resumen: pd.DataFrame,
    output_file: Path,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        entidades.to_excel(writer, sheet_name="Entidades", index=False)
        atributos.to_excel(writer, sheet_name="Atributos", index=False)
        relaciones.to_excel(writer, sheet_name="RelacionesCanon", index=False)
        resumen.to_excel(writer, sheet_name="Resumen", index=False)


def main() -> None:
    log(f"Iniciando entidades canonicas para area {AREA_ID}...")

    normalizado = encontrar_ultimo_normalizado()
    if normalizado is None:
        log("No se encontro normalizado. Ejecuta primero el script 10.")
        return

    log(f"Usando normalizado: {normalizado.name}")

    tablas = pd.read_excel(normalizado, sheet_name="Tablas")
    columnas = pd.read_excel(normalizado, sheet_name="Columnas")
    relaciones = pd.read_excel(normalizado, sheet_name="Relaciones")

    entidades_df = construir_entidades(tablas)
    atributos_df = construir_atributos(columnas)
    relaciones_df = construir_relaciones(relaciones)
    resumen_df = construir_resumen(entidades_df, atributos_df, relaciones_df)

    output_file = ENTIDADES_DIR / (
        f"11_EntidadesCanonicas_{AREA_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    exportar_salida(entidades_df, atributos_df, relaciones_df, resumen_df, output_file)

    log(f"Archivo generado: {output_file.name}")
    log(
        "Filas -> "
        f"Entidades: {len(entidades_df)}, "
        f"Atributos: {len(atributos_df)}, "
        f"Relaciones: {len(relaciones_df)}"
    )


if __name__ == "__main__":
    main()

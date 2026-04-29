"""Normalizacion de nombres y tipos sobre el diccionario consolidado."""

from pathlib import Path
from datetime import datetime
import os
import re

import pandas as pd


# =========================
# CONFIG
# =========================
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

AREA_ID_MANUAL = ""  # Ej: "OFICINA_PRESIDENCIA" para forzar el area.
AREA_ID_DEFAULT = "OFICINA_EVALUACION"
AREA_ID = (
    AREA_ID_MANUAL.strip()
    or os.getenv("PBIX_AREA", AREA_ID_DEFAULT).strip()
    or AREA_ID_DEFAULT
)

AREA_DIR = PROJECT_DIR / AREA_ID
OUTPUT_DIR = AREA_DIR / "PBIXs_output"
CONSOLIDADO_DIR = OUTPUT_DIR / "consolidado"
NORMALIZADO_DIR = OUTPUT_DIR / "normalizado"

TIPOS_MAP = {
    "int64": "bigint",
    "int32": "int",
    "int16": "smallint",
    "int8": "tinyint",
    "double": "double",
    "decimal": "decimal(38,10)",
    "currency": "decimal(18,4)",
    "string": "string",
    "boolean": "boolean",
    "datetime": "timestamp",
    "date": "date",
    "time": "time",
    "duration": "interval",
    "binary": "binary",
    "variant": "string",
    "whole number": "bigint",
    "fixed decimal number": "decimal(38,10)",
    "decimal number": "double",
    "text": "string",
    "true/false": "boolean",
}


def log(mensaje):
    """Print a timestamped message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensaje}")


def encontrar_ultimo_consolidado() -> Path | None:
    """Return the newest consolidated workbook for the active area."""
    if not CONSOLIDADO_DIR.exists():
        return None

    candidatos = sorted(CONSOLIDADO_DIR.glob("Diccionario_Consolidado_*.xlsx"))
    if not candidatos:
        return None

    return max(candidatos, key=lambda p: p.stat().st_mtime)


def normalizar_texto(valor):
    """Normalize spaces and trim textual values."""
    if pd.isna(valor):
        return valor

    texto = str(valor).strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def normalizar_identificador(valor):
    """Normalize names to snake_case style for canonical fields."""
    if pd.isna(valor):
        return valor

    texto = normalizar_texto(valor).lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    texto = re.sub(r"_+", "_", texto)
    return texto.strip("_")


def normalizar_tipo(valor):
    """Map source type labels to canonical lake-friendly types."""
    if pd.isna(valor):
        return valor

    tipo = normalizar_texto(valor).lower()
    return TIPOS_MAP.get(tipo, tipo)


def normalizar_tablas(df_tablas):
    """Add canonical columns for the Tablas sheet."""
    df = df_tablas.copy()

    if "tabla" in df.columns:
        df["tabla_canon"] = df["tabla"].apply(normalizar_identificador)

    if "tipo" in df.columns:
        df["tipo_canon"] = df["tipo"].apply(lambda v: normalizar_texto(v).upper() if not pd.isna(v) else v)

    return df


def normalizar_columnas(df_columnas):
    """Add canonical columns for the Columnas sheet."""
    df = df_columnas.copy()

    if "tabla" in df.columns:
        df["tabla_canon"] = df["tabla"].apply(normalizar_identificador)

    if "columna" in df.columns:
        df["columna_canon"] = df["columna"].apply(normalizar_identificador)

    if "tipo" in df.columns:
        df["tipo_dato_canon"] = df["tipo"].apply(normalizar_tipo)

    return df


def normalizar_medidas(df_medidas):
    """Add canonical columns for the Medidas sheet."""
    df = df_medidas.copy()

    if "tabla" in df.columns:
        df["tabla_canon"] = df["tabla"].apply(normalizar_identificador)

    if "medida" in df.columns:
        df["medida_canon"] = df["medida"].apply(normalizar_identificador)

    return df


def normalizar_relaciones(df_relaciones):
    """Add canonical columns for the Relaciones sheet."""
    df = df_relaciones.copy()

    for columna in ["tabla_origen", "tabla_destino", "columna_origen", "columna_destino"]:
        if columna in df.columns:
            df[f"{columna}_canon"] = df[columna].apply(normalizar_identificador)

    if "tipo_relacion" in df.columns:
        df["tipo_relacion_canon"] = df["tipo_relacion"].apply(
            lambda v: normalizar_texto(v).lower() if not pd.isna(v) else v
        )

    return df


def exportar_normalizado(tablas, columnas, medidas, relaciones, glosario, output_file):
    """Export normalized sheets into a single workbook."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        tablas.to_excel(writer, sheet_name="Tablas", index=False)
        columnas.to_excel(writer, sheet_name="Columnas", index=False)
        medidas.to_excel(writer, sheet_name="Medidas", index=False)
        relaciones.to_excel(writer, sheet_name="Relaciones", index=False)
        glosario.to_excel(writer, sheet_name="Glosario", index=False)


def main():
    """Normalize the latest consolidated dictionary workbook."""
    log(f"Iniciando normalizacion para {AREA_ID}...")

    consolidado_file = encontrar_ultimo_consolidado()
    if consolidado_file is None:
        log("No se encontro archivo consolidado. Ejecuta primero el script 09.")
        return

    log(f"Usando consolidado: {consolidado_file.name}")

    tablas = pd.read_excel(consolidado_file, sheet_name="Tablas")
    columnas = pd.read_excel(consolidado_file, sheet_name="Columnas")
    medidas = pd.read_excel(consolidado_file, sheet_name="Medidas")
    relaciones = pd.read_excel(consolidado_file, sheet_name="Relaciones")
    glosario = pd.read_excel(consolidado_file, sheet_name="Glosario")

    tablas_n = normalizar_tablas(tablas)
    columnas_n = normalizar_columnas(columnas)
    medidas_n = normalizar_medidas(medidas)
    relaciones_n = normalizar_relaciones(relaciones)

    output_file = NORMALIZADO_DIR / (
        f"Diccionario_Normalizado_{AREA_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

    exportar_normalizado(tablas_n, columnas_n, medidas_n, relaciones_n, glosario, output_file)

    log(f"Normalizacion completada: {output_file.name}")
    log(
        "Filas -> "
        f"Tablas: {len(tablas_n)}, "
        f"Columnas: {len(columnas_n)}, "
        f"Medidas: {len(medidas_n)}, "
        f"Relaciones: {len(relaciones_n)}, "
        f"Glosario: {len(glosario)}"
    )


if __name__ == "__main__":
    main()

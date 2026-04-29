"""Genera especificacion minima de capa Bronze para trazabilidad."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os

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
BRONZE_DIR = SILVER_DIR / "bronze_minima"


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


def construir_bronze_objetos(tablas: pd.DataFrame) -> pd.DataFrame:
    df = tablas.copy()
    for c in ["tabla", "tabla_canon", "pbix_source"]:
        if c not in df.columns:
            df[c] = None

    df = df[["tabla", "tabla_canon", "pbix_source"]].drop_duplicates().reset_index(drop=True)
    df["bronze_objeto"] = "bronze_" + df["tabla_canon"].fillna(df["tabla"]).astype(str)
    df["modo_ingesta"] = "snapshot"
    df["llave_trazabilidad"] = df["pbix_source"].astype(str) + "::" + df["tabla"].astype(str)

    return df[["bronze_objeto", "tabla", "tabla_canon", "pbix_source", "modo_ingesta", "llave_trazabilidad"]]


def construir_bronze_columnas(columnas: pd.DataFrame) -> pd.DataFrame:
    df = columnas.copy()
    for c in ["tabla", "tabla_canon", "columna", "columna_canon", "tipo_dato_canon", "pbix_source"]:
        if c not in df.columns:
            df[c] = None

    df = df[
        ["tabla", "tabla_canon", "columna", "columna_canon", "tipo_dato_canon", "pbix_source"]
    ].drop_duplicates().reset_index(drop=True)

    df["bronze_objeto"] = "bronze_" + df["tabla_canon"].fillna(df["tabla"]).astype(str)
    df["bronze_campo"] = df["columna_canon"].fillna(df["columna"])
    df["preservar_raw"] = True

    return df[
        [
            "bronze_objeto",
            "bronze_campo",
            "tipo_dato_canon",
            "tabla",
            "columna",
            "pbix_source",
            "preservar_raw",
        ]
    ]


def exportar_salida(objetos: pd.DataFrame, columnas: pd.DataFrame, excel_file: Path, csv_file: Path) -> None:
    excel_file.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        objetos.to_excel(writer, sheet_name="BronzeObjetos", index=False)
        columnas.to_excel(writer, sheet_name="BronzeColumnas", index=False)

    columnas.to_csv(csv_file, index=False, encoding="utf-8")


def main() -> None:
    log(f"Iniciando Bronze minima para area {AREA_ID}...")

    normalizado_file = encontrar_ultimo_normalizado()
    if normalizado_file is None:
        log("No se encontro normalizado. Ejecuta primero el script 10.")
        return

    log(f"Usando normalizado: {normalizado_file.name}")

    tablas = pd.read_excel(normalizado_file, sheet_name="Tablas")
    columnas = pd.read_excel(normalizado_file, sheet_name="Columnas")

    bronze_objetos = construir_bronze_objetos(tablas)
    bronze_columnas = construir_bronze_columnas(columnas)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = BRONZE_DIR / f"15_BronzeMinima_{AREA_ID}_{stamp}.xlsx"
    csv_file = BRONZE_DIR / f"15_BronzeMinima_{AREA_ID}_{stamp}.csv"

    exportar_salida(bronze_objetos, bronze_columnas, excel_file, csv_file)

    log(f"Archivo Excel generado: {excel_file.name}")
    log(f"Archivo CSV generado: {csv_file.name}")
    log(
        "Filas -> "
        f"Objetos: {len(bronze_objetos)}, "
        f"Columnas: {len(bronze_columnas)}"
    )


if __name__ == "__main__":
    main()

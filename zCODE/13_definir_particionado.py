"""Propone estrategia de particionado para entidades Silver."""

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
SILVER_DIR = OUTPUT_DIR / "silver"
ENTIDADES_DIR = SILVER_DIR / "entidades"
PARTICIONADO_DIR = SILVER_DIR / "particionado"


DATE_TYPES = {"date", "timestamp", "datetime"}
DATE_HINTS = ("fecha", "date", "periodo", "mes", "anio", "year")


def log(mensaje: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {mensaje}")


def encontrar_ultimo_entidades() -> Path | None:
    if not ENTIDADES_DIR.exists():
        return None
    candidatos = sorted(ENTIDADES_DIR.glob("11_EntidadesCanonicas_*.xlsx"))
    if not candidatos:
        return None
    return max(candidatos, key=lambda p: p.stat().st_mtime)


def _es_columna_fecha(nombre: str, tipo: str) -> bool:
    n = str(nombre or "").lower()
    t = str(tipo or "").lower()
    return t in DATE_TYPES or any(h in n for h in DATE_HINTS)


def recomendar_particiones(entidades: pd.DataFrame, atributos: pd.DataFrame) -> pd.DataFrame:
    recomendaciones = []

    for _, ent in entidades.iterrows():
        entidad = ent.get("entidad")
        entidad_tipo = ent.get("entidad_tipo", "desconocida")
        cols = atributos[atributos["entidad"] == entidad].copy()

        if cols.empty:
            recomendaciones.append(
                {
                    "entidad": entidad,
                    "entidad_tipo": entidad_tipo,
                    "estrategia": "sin_particion",
                    "columna_particion": None,
                    "granularidad": None,
                    "justificacion": "No hay atributos para inferir.",
                }
            )
            continue

        cols["es_fecha"] = cols.apply(
            lambda r: _es_columna_fecha(r.get("atributo"), r.get("tipo_dato_canon")), axis=1
        )
        fechas = cols[cols["es_fecha"] == True]  # noqa: E712

        if fechas.empty:
            recomendaciones.append(
                {
                    "entidad": entidad,
                    "entidad_tipo": entidad_tipo,
                    "estrategia": "sin_particion",
                    "columna_particion": None,
                    "granularidad": None,
                    "justificacion": "No se encontro columna temporal candidata.",
                }
            )
            continue

        elegida = fechas.sort_values(by="atributo").iloc[0]
        columna = elegida.get("atributo")

        if str(entidad_tipo).lower() == "fact":
            estrategia = "particion_tiempo"
            granularidad = "mensual"
            justificacion = "Entidad tipo fact con columna temporal candidata."
        else:
            estrategia = "particion_tiempo_liviana"
            granularidad = "trimestral"
            justificacion = "Entidad no-fact con columna temporal; se sugiere baja cardinalidad."

        recomendaciones.append(
            {
                "entidad": entidad,
                "entidad_tipo": entidad_tipo,
                "estrategia": estrategia,
                "columna_particion": columna,
                "granularidad": granularidad,
                "justificacion": justificacion,
            }
        )

    return pd.DataFrame(recomendaciones)


def exportar_salida(df: pd.DataFrame, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Particionado", index=False)


def main() -> None:
    log(f"Iniciando recomendaciones de particionado para area {AREA_ID}...")

    entidades_file = encontrar_ultimo_entidades()
    if entidades_file is None:
        log("No se encontro salida del script 11. Ejecuta primero 11_entidades_canonicas.py")
        return

    log(f"Usando archivo: {entidades_file.name}")

    entidades = pd.read_excel(entidades_file, sheet_name="Entidades")
    atributos = pd.read_excel(entidades_file, sheet_name="Atributos")

    recomendaciones = recomendar_particiones(entidades, atributos)

    output_file = PARTICIONADO_DIR / (
        f"13_ParticionadoSilver_{AREA_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    exportar_salida(recomendaciones, output_file)

    log(f"Archivo generado: {output_file.name}")
    log(f"Filas recomendaciones: {len(recomendaciones)}")


if __name__ == "__main__":
    main()

"""Define propuesta de historizacion para entidades Silver."""

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
HISTORIZACION_DIR = SILVER_DIR / "historizacion"


HINTS_SCD2 = ("vigencia", "version", "desde", "hasta", "inicio", "fin")
HINTS_AUDIT = ("actualizacion", "actualizado", "modificacion", "estado", "activo")


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


def definir_estrategia(entidad_tipo: str, atributos_entidad: list[str]) -> tuple[str, str]:
    joined = " ".join(atributos_entidad).lower()

    if entidad_tipo == "fact":
        return "append_only", "Entidad tipo fact; historizacion por insercion incremental."

    if any(h in joined for h in HINTS_SCD2):
        return "scd2", "Se detectan columnas de vigencia/version para cambios historicos."

    if any(h in joined for h in HINTS_AUDIT):
        return "scd1", "Se detectan columnas de auditoria/estado sin ventana explicita."

    return "sin_historizacion", "No se detectan indicios de historizacion."


def construir_historizacion(entidades: pd.DataFrame, atributos: pd.DataFrame) -> pd.DataFrame:
    filas = []

    for _, ent in entidades.iterrows():
        entidad = ent.get("entidad")
        entidad_tipo = str(ent.get("entidad_tipo", "desconocida")).lower()

        attrs = atributos[atributos["entidad"] == entidad]["atributo"].dropna().astype(str).tolist()
        estrategia, razon = definir_estrategia(entidad_tipo, attrs)

        filas.append(
            {
                "entidad": entidad,
                "entidad_tipo": entidad_tipo,
                "estrategia_historizacion": estrategia,
                "justificacion": razon,
                "campos_relevantes": ", ".join(sorted(attrs)[:10]) if attrs else None,
            }
        )

    return pd.DataFrame(filas)


def exportar_salida(df: pd.DataFrame, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Historizacion", index=False)


def main() -> None:
    log(f"Iniciando propuesta de historizacion para area {AREA_ID}...")

    entidades_file = encontrar_ultimo_entidades()
    if entidades_file is None:
        log("No se encontro salida del script 11. Ejecuta primero 11_entidades_canonicas.py")
        return

    log(f"Usando archivo: {entidades_file.name}")

    entidades = pd.read_excel(entidades_file, sheet_name="Entidades")
    atributos = pd.read_excel(entidades_file, sheet_name="Atributos")

    historizacion = construir_historizacion(entidades, atributos)

    output_file = HISTORIZACION_DIR / (
        f"14_HistorizacionSilver_{AREA_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    exportar_salida(historizacion, output_file)

    log(f"Archivo generado: {output_file.name}")
    log(f"Filas recomendaciones: {len(historizacion)}")


if __name__ == "__main__":
    main()

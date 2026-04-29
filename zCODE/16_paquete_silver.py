"""Empaqueta los ultimos artefactos de modelado Silver."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import os
import shutil


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
PAQUETES_DIR = SILVER_DIR / "paquetes"


def log(mensaje: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {mensaje}")


def ultimo_archivo(glob_pattern: str) -> Path | None:
    candidatos = sorted(OUTPUT_DIR.glob(glob_pattern))
    if not candidatos:
        return None
    return max(candidatos, key=lambda p: p.stat().st_mtime)


def ultimo_archivo_silver(subdir: str, glob_pattern: str) -> Path | None:
    carpeta = SILVER_DIR / subdir
    if not carpeta.exists():
        return None

    candidatos = sorted(carpeta.glob(glob_pattern))
    if not candidatos:
        return None

    return max(candidatos, key=lambda p: p.stat().st_mtime)


def recolectar_artefactos() -> list[Path]:
    artefactos: list[Path] = []

    mapa = [
        ultimo_archivo("consolidado/Diccionario_Consolidado_*.xlsx"),
        ultimo_archivo("normalizado/Diccionario_Normalizado_*.xlsx"),
        ultimo_archivo_silver("entidades", "11_EntidadesCanonicas_*.xlsx"),
        ultimo_archivo_silver("claves", "12_ClavesCanonicas_*.xlsx"),
        ultimo_archivo_silver("particionado", "13_ParticionadoSilver_*.xlsx"),
        ultimo_archivo_silver("historizacion", "14_HistorizacionSilver_*.xlsx"),
        ultimo_archivo_silver("bronze_minima", "15_BronzeMinima_*.xlsx"),
        ultimo_archivo_silver("bronze_minima", "15_BronzeMinima_*.csv"),
    ]

    for item in mapa:
        if item is not None and item.exists():
            artefactos.append(item)

    return artefactos


def escribir_manifest(artefactos: list[Path], package_dir: Path) -> Path:
    filas = []
    for f in artefactos:
        rel = f.relative_to(AREA_DIR)
        filas.append(
            {
                "archivo": str(rel).replace("\\", "/"),
                "tamano_bytes": f.stat().st_size,
                "modificado": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            }
        )

    payload = {
        "area_id": AREA_ID,
        "generado_en": datetime.now().isoformat(),
        "total_artefactos": len(filas),
        "artefactos": filas,
    }

    manifest = package_dir / "manifest_silver.json"
    manifest.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return manifest


def copiar_artefactos(artefactos: list[Path], package_dir: Path) -> None:
    for f in artefactos:
        destino = package_dir / f.name
        shutil.copy2(f, destino)


def main() -> None:
    log(f"Iniciando paquete Silver para area {AREA_ID}...")

    artefactos = recolectar_artefactos()
    if not artefactos:
        log("No se encontraron artefactos para empaquetar.")
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_dir = PAQUETES_DIR / f"SilverPackage_{AREA_ID}_{stamp}"
    package_dir.mkdir(parents=True, exist_ok=True)

    copiar_artefactos(artefactos, package_dir)
    manifest = escribir_manifest(artefactos, package_dir)

    zip_base = str(package_dir)
    zip_file = shutil.make_archive(zip_base, "zip", root_dir=package_dir)

    log(f"Paquete generado: {package_dir.name}")
    log(f"ZIP generado: {Path(zip_file).name}")
    log(f"Manifest generado: {manifest.name}")
    log(f"Artefactos incluidos: {len(artefactos)}")


if __name__ == "__main__":
    main()

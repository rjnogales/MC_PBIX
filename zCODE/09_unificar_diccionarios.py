"""Consolidación de diccionarios técnicos de múltiples PBIXs en un catálogo único."""

from pathlib import Path
import pandas as pd
import os
from datetime import datetime


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
PBIX_DIR = AREA_DIR / "PBIXs"
OUTPUT_DIR = AREA_DIR / "PBIXs_output"
PBIX_DICCIONARIOS_DIR = OUTPUT_DIR / "diccionarios_pbix"
CONSOLIDADO_DIR = OUTPUT_DIR / "consolidado"
CONSOLIDADO_FILE = CONSOLIDADO_DIR / f"Diccionario_Consolidado_{AREA_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"


def log(mensaje):
    """Print a timestamped message.

    Args:
        mensaje: Message to display.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensaje}")


def nombres_pbix_validos(pbix_dir):
    """Return the stems of all PBIX files found in the input directory.

    Args:
        pbix_dir: Directory containing the source .pbix files.

    Returns:
        set[str]: Set of PBIX stems (filename without extension).
    """
    if not pbix_dir.exists():
        log(f"⚠️  Directorio PBIXs no existe: {pbix_dir}")
        return set()
    return {p.stem for p in pbix_dir.glob("*.pbix")}


def descubrir_excels(output_dir, pbix_validos):
    """Discover Excel catalogs that have a matching source PBIX.

    Args:
        output_dir: Directory containing individual PBIX Excel files.
        pbix_validos: Set of valid PBIX stems from the input directory.

    Returns:
        list[Path]: Sorted list of Excel files with a PBIX origin.
    """
    if not output_dir.exists():
        log(f"❌ Directorio {output_dir} no existe.")
        return []

    todos = sorted(output_dir.glob("*.xlsx"))
    excels = [f for f in todos if f.stem in pbix_validos]
    omitidos = [f.name for f in todos if f.stem not in pbix_validos]

    if omitidos:
        log(f"⚠️  Omitidos {len(omitidos)} archivos sin PBIX de origen: {omitidos}")

    log(f"✓ Encontrados {len(excels)} diccionarios con PBIX de origen en {output_dir}")
    return excels


def leer_hoja_con_origen(excel_file, sheet_name, pbix_name):
    """Read a sheet from an Excel file and add source tracking.

    Args:
        excel_file: Path to Excel file.
        sheet_name: Name of the sheet to read.
        pbix_name: Original PBIX file name for traceability.

    Returns:
        pd.DataFrame | None: Sheet data with pbix_source column, or None if sheet missing.
    """
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        df["pbix_source"] = pbix_name
        return df
    except ValueError:
        # Sheet does not exist in this Excel.
        return None
    except Exception as e:
        log(f"⚠️  Error leyendo {sheet_name} de {excel_file.name}: {e}")
        return None


def consolidar_diccionarios(excels):
    """Consolidate all PBIX Excel catalogs into unified DataFrames.

    Args:
        excels: List of Excel file paths to consolidate.

    Returns:
        dict: Consolidated DataFrames keyed by sheet name (tablas, columnas, medidas, relaciones, glosario).
    """
    hojas_esperadas = ["Tablas", "Columnas", "Medidas", "Relaciones", "Glosario"]
    consolidado = {hoja.lower(): [] for hoja in hojas_esperadas}

    for excel_file in excels:
        pbix_name = excel_file.stem
        log(f"  → Procesando {pbix_name}...")

        for hoja in hojas_esperadas:
            df = leer_hoja_con_origen(excel_file, hoja, pbix_name)
            if df is not None:
                consolidado[hoja.lower()].append(df)

    # Consolidate each sheet by concatenating all rows.
    resultado = {}
    for hoja, dataframes in consolidado.items():
        if dataframes:
            df_consolidado = pd.concat(dataframes, ignore_index=True)
            resultado[hoja] = df_consolidado
            log(f"✓ {hoja.capitalize()}: {len(df_consolidado)} filas consolidadas")
        else:
            log(f"⚠️  {hoja.capitalize()}: sin datos")
            resultado[hoja] = pd.DataFrame()

    return resultado


def exportar_consolidado(consolidado, output_file):
    """Export consolidated DataFrames to a single Excel workbook.

    Args:
        consolidado: Dictionary of consolidated DataFrames by sheet name.
        output_file: Output Excel file path.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            for hoja, df in consolidado.items():
                df.to_excel(writer, sheet_name=hoja.capitalize(), index=False)

        log(f"✓ Diccionario consolidado exportado a {output_file.name}")
    except Exception as e:
        log(f"❌ Error exportando consolidado: {e}")
        raise


def main():
    """Main entry point."""
    log(f"🔍 Unificando diccionarios de {AREA_ID}...")

    # Only consolidate Excels whose source PBIX exists in PBIXs/.
    pbix_validos = nombres_pbix_validos(PBIX_DIR)
    excels = descubrir_excels(PBIX_DICCIONARIOS_DIR, pbix_validos)
    if not excels:
        log("❌ No se encontraron diccionarios para consolidar.")
        return

    # Consolidate all sheets.
    consolidado = consolidar_diccionarios(excels)

    # Export unified catalog.
    exportar_consolidado(consolidado, CONSOLIDADO_FILE)
    log(f"✅ Proceso completado.")


if __name__ == "__main__":
    main()

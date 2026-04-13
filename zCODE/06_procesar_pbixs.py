"""Orquestador principal para procesar PBIX por area y generar catalogos Excel."""

from pathlib import Path
import subprocess
import pandas as pd
import importlib.util
import json
import shutil
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
CONFIG_FILE = AREA_DIR / "config" / "pipeline.json"

DEFAULT_CONFIG = {
    "area_id": AREA_ID,
    "paths": {
        "pbix_in": "PBIXs",
        "pbix_descompuestos": "PBIXs_descompuestos",
        "output": "PBIXs_output",
        "log_file": "proceso_pbix.log",
    },
}


def cargar_config_area(config_file):
    """Carga y valida la configuracion de area desde config/pipeline.json."""
    config = {
        "area_id": DEFAULT_CONFIG["area_id"],
        "paths": dict(DEFAULT_CONFIG["paths"]),
    }

    if not config_file.exists():
        return config

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"⚠️ Config inválida en {config_file}: {e}. Se usarán valores por defecto.")
        return config

    if isinstance(data, dict):
        area_name = data.get("area_id")
        if isinstance(area_name, str) and area_name.strip():
            config["area_id"] = area_name.strip()

        paths = data.get("paths")
        if isinstance(paths, dict):
            for key in config["paths"]:
                value = paths.get(key)
                if isinstance(value, str) and value.strip():
                    config["paths"][key] = value.strip()

    return config


def resolver_ruta_area(base_dir, path_value):
    """Resuelve rutas relativas al directorio del area activa."""
    ruta = Path(path_value)
    if ruta.is_absolute():
        return ruta
    return base_dir / ruta


AREA_CONFIG = cargar_config_area(CONFIG_FILE)

PBIX_DIR = resolver_ruta_area(AREA_DIR, AREA_CONFIG["paths"]["pbix_in"])
DESCOMP_DIR = resolver_ruta_area(AREA_DIR, AREA_CONFIG["paths"]["pbix_descompuestos"])
PBIX_OUTPUT_DIR = resolver_ruta_area(AREA_DIR, AREA_CONFIG["paths"]["output"])
EXTRACT_META_FILENAME = ".extract_meta.json"

LOG_FILE = resolver_ruta_area(AREA_DIR, AREA_CONFIG["paths"]["log_file"])


# =========================
# LOGGING SIMPLE
# =========================
def log(mensaje):
    """Escribe mensaje en consola y en el archivo de log del area."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] {mensaje}"

    print(linea)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linea + "\n")


# =========================
# UTIL
# =========================
def cargar_funcion(script, funcion):
    """Carga dinamicamente una funcion desde otro script en zCODE."""
    spec = importlib.util.spec_from_file_location(script, SCRIPT_DIR / script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, funcion)


def construir_firma_pbix(pbix_file):
    """Construye una firma de control para detectar cambios en el PBIX."""
    stats = pbix_file.stat()
    return {
        "pbix_name": pbix_file.name,
        "pbix_path": str(pbix_file.resolve()),
        "pbix_size": stats.st_size,
        "pbix_mtime_ns": stats.st_mtime_ns,
    }


def leer_metadata_extraccion(destino):
    """Lee metadata de extraccion previa si existe y es valida."""
    meta_file = destino / EXTRACT_META_FILENAME

    if not meta_file.exists():
        return None

    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        log(f"⚠️ Metadata inválida en {meta_file.name}: {e}")
        return None


def guardar_metadata_extraccion(destino, firma_pbix):
    """Guarda metadata de extraccion para reutilizacion incremental."""
    meta_file = destino / EXTRACT_META_FILENAME

    payload = {
        **firma_pbix,
        "extracted_at": datetime.now().isoformat(timespec="seconds")
    }

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def metadata_corresponde_pbix(metadata, firma_pbix):
    """Valida si la metadata corresponde exactamente al PBIX actual."""
    return (
        metadata.get("pbix_name") == firma_pbix["pbix_name"]
        and str(metadata.get("pbix_path", "")).casefold() == firma_pbix["pbix_path"].casefold()
        and metadata.get("pbix_size") == firma_pbix["pbix_size"]
        and metadata.get("pbix_mtime_ns") == firma_pbix["pbix_mtime_ns"]
    )


def eliminar_descomposicion(destino):
    """Elimina una carpeta de descomposicion previa."""
    try:
        shutil.rmtree(destino)
        return True
    except OSError as e:
        log(f"❌ No se pudo limpiar {destino.name}: {e}")
        return False


def referencia_mtime_descomposicion(destino):
    """Obtiene referencia temporal para comparar vigencia de descomposicion."""
    version_file = destino / "Version.txt"

    if version_file.exists():
        return version_file.stat().st_mtime_ns

    return destino.stat().st_mtime_ns


def ejecutar_extract_pbitools(pbix_file, destino):
    """Ejecuta pbi-tools extract y retorna la ruta final de descomposicion."""
    # pbi-tools Desktop 1.2.0 no acepta -o; extrae por defecto junto al PBIX.
    salida_default = pbix_file.with_suffix("")

    if salida_default.exists() and not eliminar_descomposicion(salida_default):
        return None

    subprocess.run([
        "pbi-tools",
        "extract",
        str(pbix_file)
    ], check=True)

    if not salida_default.exists():
        raise FileNotFoundError(f"No se encontró salida de pbi-tools: {salida_default}")

    if salida_default.resolve() == destino.resolve():
        return salida_default

    if destino.exists() and not eliminar_descomposicion(destino):
        log(f"⚠️ No se pudo limpiar {destino.name}; se usará salida en PBIXs")
        return salida_default

    try:
        shutil.move(str(salida_default), str(destino))
        return destino
    except (OSError, shutil.Error) as e:
        log(f"⚠️ No se pudo mover extracción a {destino.name}; se usará PBIXs: {e}")
        return salida_default


# =========================
# PBI-TOOLS
# =========================
def descomponer_pbix(pbix_file):
    """Reutiliza descomposicion vigente o extrae nuevamente cuando hay cambios."""
    destino = DESCOMP_DIR / pbix_file.stem
    salida_default = pbix_file.with_suffix("")
    candidatos = [destino]
    if salida_default != destino:
        candidatos.append(salida_default)

    firma_pbix = construir_firma_pbix(pbix_file)

    for candidato in candidatos:
        if not candidato.exists():
            continue

        model_dir = candidato / "Model"
        tables_dir = model_dir / "tables"

        if not model_dir.exists() or not tables_dir.exists():
            log(f"⚠️ Carpeta incompleta detectada en {candidato.name}; se ignorará")
            continue

        metadata = leer_metadata_extraccion(candidato)

        if metadata and metadata_corresponde_pbix(metadata, firma_pbix):
            log(f"♻️ Descomposición vigente: {pbix_file.name} ({candidato.name})")
            return candidato

        if metadata is None:
            ref_mtime = referencia_mtime_descomposicion(candidato)

            if ref_mtime >= firma_pbix["pbix_mtime_ns"]:
                log(f"♻️ Descomposición vigente (sin metadata previa): {pbix_file.name} ({candidato.name})")
                guardar_metadata_extraccion(candidato, firma_pbix)
                return candidato

            log(f"🔄 Sin metadata y PBIX más reciente en {pbix_file.name} ({candidato.name})")
            continue

        log(f"🔄 PBIX actualizado detectado en {pbix_file.name} ({candidato.name})")

    log(f"📦 Descomponiendo: {pbix_file.name}")

    try:
        ruta_extraida = ejecutar_extract_pbitools(pbix_file, destino)
        if ruta_extraida is None:
            return None

        guardar_metadata_extraccion(ruta_extraida, firma_pbix)

        log("✅ Descomposición OK")

    except FileNotFoundError as e:
        log(f"❌ pbi-tools no encontrado: {e}")
        return None
    except subprocess.CalledProcessError as e:
        log(f"❌ Error descomponiendo {pbix_file.name}: {e}")
        return None
    except OSError as e:
        log(f"❌ Error guardando metadata de {pbix_file.name}: {e}")
        return None

    return ruta_extraida


# =========================
# PROCESAR UN PBIX
# =========================
def procesar_pbix(pbix_file, leer_tablas, leer_columnas, leer_medidas, leer_relaciones, exportar_excel, indice=None, total=None):
    """Procesa un PBIX: descompone, extrae metadatos y exporta Excel."""

    if indice is not None and total is not None:
        log(f"🚀 [{indice}/{total}] Procesando: {pbix_file.name}")
    else:
        log(f"🚀 Procesando: {pbix_file.name}")

    try:
        ruta = descomponer_pbix(pbix_file)

        if ruta is None:
            log(f"⛔ Se omite por error en descomposición: {pbix_file.name}")
            return False

        if not (ruta / "Model").exists():
            log(f"⚠️ Sin carpeta Model: {pbix_file.name}")
            return False

        if not (ruta / "Model" / "tables").exists():
            log(f"⚠️ Sin carpeta Model/tables: {pbix_file.name}")
            return False

        # =========================
        # EXTRACCIÓN
        # =========================
        tablas = pd.DataFrame({"tabla": leer_tablas(str(ruta))})
        columnas = pd.DataFrame(leer_columnas(str(ruta)))
        medidas = pd.DataFrame(leer_medidas(str(ruta)))
        relaciones = pd.DataFrame(leer_relaciones(str(ruta)))

        log(f"📊 Tablas: {len(tablas)} | Columnas: {len(columnas)} | Medidas: {len(medidas)}")

        # =========================
        # EXPORTACIÓN
        # =========================
        output_file = PBIX_OUTPUT_DIR / f"{ruta.name}.xlsx"

        exportar_excel(tablas, columnas, medidas, relaciones, output_file)

        log(f"✅ Excel generado: {output_file.name}")
        return True

    except Exception as e:
        log(f"❌ Error procesando {pbix_file.name}: {e}")
        return False


# =========================
# MAIN
# =========================
def main():
    """Punto de entrada del proceso masivo por area activa."""

    log("======================================")
    log("🚀 INICIO PROCESO MASIVO PBIX")
    log(f"🏢 Área activa: {AREA_CONFIG['area_id']}")
    log(f"⚙️ Config usada: {CONFIG_FILE}")
    log("======================================")

    if not PBIX_DIR.exists():
        log(f"❌ No existe carpeta de entrada para el área: {PBIX_DIR}")
        return

    DESCOMP_DIR.mkdir(parents=True, exist_ok=True)
    PBIX_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar funciones una sola vez
    leer_tablas = cargar_funcion("01_leer_tablas.py", "leer_tablas")
    leer_columnas = cargar_funcion("02_leer_columnas.py", "leer_columnas")
    leer_medidas = cargar_funcion("03_leer_medidas.py", "leer_medidas")
    leer_relaciones = cargar_funcion("04_leer_relaciones.py", "leer_relaciones")
    exportar_excel = cargar_funcion("05_exportar_excel.py", "exportar_excel")

    pbix_files = sorted(PBIX_DIR.glob("*.pbix"), key=lambda p: p.name.casefold())

    if not pbix_files:
        log("⚠️ No se encontraron archivos PBIX")
        return

    log(f"📁 Total PBIX encontrados: {len(pbix_files)}")

    log("📋 Listado de PBIX a procesar:")
    for i, pbix in enumerate(pbix_files, start=1):
        log(f"   {i}. {pbix.name}")

    total = len(pbix_files)
    exitosos = 0

    for i, pbix in enumerate(pbix_files, start=1):
        ok = procesar_pbix(
            pbix,
            leer_tablas,
            leer_columnas,
            leer_medidas,
            leer_relaciones,
            exportar_excel,
            indice=i,
            total=total,
        )
        if ok:
            exitosos += 1

    log(f"📌 Resumen: {exitosos} OK | {total - exitosos} con error")

    log("======================================")
    log("🎯 PROCESO FINALIZADO")
    log("======================================")


if __name__ == "__main__":
    main()
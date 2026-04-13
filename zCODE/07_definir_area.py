"""Lanzador de ejecucion por area: valida insumos y ejecuta 06_procesar_pbixs.py."""

from pathlib import Path
import os
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
PROCESO_SCRIPT = SCRIPT_DIR / "06_procesar_pbixs.py"


def imprimir_uso():
    """Imprime ayuda de uso en linea de comando."""
    print("Uso: python zCODE/07_definir_area.py <AREA_ID>")
    print("Ejemplo: python zCODE/07_definir_area.py OFICINA_EVALUACION")


def main():
    """Recibe AREA_ID, valida estructura y dispara el proceso principal."""
    if len(sys.argv) != 2 or sys.argv[1] in {"-h", "--help"}:
        imprimir_uso()
        return 1

    area_id = sys.argv[1].strip()
    if not area_id:
        print("Error: AREA_ID no puede estar vacio.")
        imprimir_uso()
        return 1

    area_dir = PROJECT_DIR / area_id
    config_file = area_dir / "config" / "pipeline.json"

    if not area_dir.exists() or not area_dir.is_dir():
        print(f"Error: no existe el area '{area_id}' en {PROJECT_DIR}.")
        return 2

    if not config_file.exists():
        print(f"Error: falta archivo de configuracion: {config_file}")
        print("Cada area debe tener su propio config/pipeline.json.")
        return 3

    env = os.environ.copy()
    env["PBIX_AREA"] = area_id

    cmd = [sys.executable, str(PROCESO_SCRIPT)]
    print(f"Ejecutando area: {area_id}")
    print(f"Comando: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=str(PROJECT_DIR), env=env)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

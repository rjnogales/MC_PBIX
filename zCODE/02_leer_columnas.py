"""Extraccion de columnas y tipo de dato desde archivos .tmdl."""

import os
import re


def leer_columnas(ruta_pbix):
    """
    Extrae columnas por tabla desde Model/tables.

    Parametros:
        ruta_pbix (str): Ruta raiz del PBIX descompuesto.

    Retorna:
        list[dict]: Registros con tabla, columna y tipo.
    """
    ruta_tablas = os.path.join(ruta_pbix, "Model", "tables")

    if not os.path.exists(ruta_tablas):
        raise FileNotFoundError(f"No existe la ruta: {ruta_tablas}")

    resultado = []

    for archivo in os.listdir(ruta_tablas):

        if not archivo.endswith(".tmdl"):
            continue

        tabla = archivo.replace(".tmdl", "")

        # excluir técnicas
        if tabla.startswith("LocalDateTable") or tabla.startswith("DateTableTemplate"):
            continue

        ruta_archivo = os.path.join(ruta_tablas, archivo)

        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()

        col_actual = None

        for linea in lineas:

            linea = linea.strip()

            # detectar inicio de columna
            if linea.startswith("column "):
                col_actual = linea.replace("column ", "").strip()

            # detectar tipo
            elif "dataType:" in linea and col_actual:
                tipo = linea.split("dataType:")[1].strip()

                resultado.append({
                    "tabla": tabla,
                    "columna": col_actual,
                    "tipo": tipo
                })

                col_actual = None  # reset

    return resultado


# Prueba local rapida
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(base_dir, "OFICINA_EVALUACION", "PBIXs_descompuestos", "LN_IndicadoresRutasMIO")

    columnas = leer_columnas(ruta)

    print("\n📊 Columnas encontradas:\n")

    for c in columnas[:20]:
        print(f"{c['tabla']} | {c['columna']} | {c['tipo']}")

    print(f"\nTotal columnas: {len(columnas)}")
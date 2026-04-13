"""Extraccion de tablas desde un PBIX descompuesto con pbi-tools."""
"""https://pbi.tools/"""

import os


def leer_tablas(ruta_pbix):
    """
    Lee las tablas del modelo semantico desde Model/tables.

    Parametros:
        ruta_pbix (str): Ruta raiz del PBIX descompuesto.

    Retorna:
        list[str]: Nombres de tablas no tecnicas encontradas.
    """

    ruta_tablas = os.path.join(ruta_pbix, "Model", "tables")

    if not os.path.exists(ruta_tablas):
        raise FileNotFoundError(f"No existe la ruta: {ruta_tablas}")

    tablas = []

    for archivo in os.listdir(ruta_tablas):
        if archivo.endswith(".tmdl"):
            nombre = archivo.replace(".tmdl", "")

            # excluir tablas técnicas
            if nombre.startswith("LocalDateTable"):
                continue
            if nombre.startswith("DateTableTemplate"):
                continue

            tablas.append(nombre)

    return tablas


# Prueba local rapida
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(base_dir, "OFICINA_EVALUACION", "PBIXs_descompuestos", "LN_IndicadoresRutasMIO")
    resultado = leer_tablas(ruta)

    print("\n📊 Tablas encontradas:")
    for t in resultado:
        print(f"- {t}")
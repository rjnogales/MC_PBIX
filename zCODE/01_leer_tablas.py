"""Extraccion de tablas desde un PBIX descompuesto con pbi-tools."""
"""https://pbi.tools/"""

import os


def leer_tablas(ruta_pbix):
    """Read semantic model tables from Model/tables.

    Args:
        ruta_pbix: Root path of the decomposed PBIX structure.

    Returns:
        list[str]: Names of non-technical tables found in the model.

    Raises:
        FileNotFoundError: If Model/tables does not exist.
    """

    ruta_tablas = os.path.join(ruta_pbix, "Model", "tables")

    # La extraccion depende de la estructura generada por pbi-tools.
    if not os.path.exists(ruta_tablas):
        raise FileNotFoundError(f"No existe la ruta: {ruta_tablas}")

    tablas = []

    for archivo in os.listdir(ruta_tablas):
        if archivo.endswith(".tmdl"):
            # Cada archivo .tmdl representa una tabla del modelo.
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
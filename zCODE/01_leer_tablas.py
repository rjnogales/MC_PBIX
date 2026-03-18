import os


def leer_tablas(ruta_pbix):
    """
    Lee las tablas desde un PBIX extraído con pbi-tools.

    Parámetro:
        ruta_pbix (str): ruta raíz del proyecto extraído

    Retorna:
        list: lista de tablas encontradas
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


# 🔍 prueba rápida
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(base_dir, "LN_IndicadoresRutasMIO")
    resultado = leer_tablas(ruta)

    print("\n📊 Tablas encontradas:")
    for t in resultado:
        print(f"- {t}")
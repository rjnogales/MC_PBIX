import os


def limpiar_dax(dax):

    cortes = [
        "changedProperty",
        "annotation",
        "column ",
        "formatString",
        "dataType"
    ]

    for corte in cortes:
        if corte in dax:
            dax = dax.split(corte)[0]

    # 🔧 limpiar "=" repetidos
    dax = dax.strip()

    while dax.startswith("="):
        dax = dax[1:].strip()

    return dax


def leer_medidas(ruta_pbix):

    ruta_tablas = os.path.join(ruta_pbix, "Model", "tables")

    if not os.path.exists(ruta_tablas):
        raise FileNotFoundError(f"No existe la ruta: {ruta_tablas}")

    resultado = []

    for archivo in os.listdir(ruta_tablas):

        if not archivo.endswith(".tmdl"):
            continue

        tabla = archivo.replace(".tmdl", "")

        ruta_archivo = os.path.join(ruta_tablas, archivo)

        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()

        medida_actual = None
        dax_acumulado = []

        for linea in lineas:
            linea_strip = linea.strip()

            # inicio medida
            if linea_strip.startswith("measure "):
                medida_actual = linea_strip.replace("measure ", "").strip()
                dax_acumulado = []

            # expresión
            elif "expression:" in linea_strip and medida_actual:
                dax_line = linea_strip.split("expression:")[1].strip()
                dax_acumulado.append(dax_line)

            elif medida_actual:
                dax_acumulado.append(linea_strip)

                # cierre heurístico
                if linea_strip.endswith(")"):
                    dax = " ".join(dax_acumulado)
                    dax = limpiar_dax(dax)

                    resultado.append({
                        "tabla": tabla,
                        "medida": medida_actual,
                        "dax": dax
                    })

                    medida_actual = None
                    dax_acumulado = []

    return resultado


# 🔍 prueba
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(base_dir, "LN_IndicadoresRutasMIO")

    medidas = leer_medidas(ruta)

    print("\n📊 Medidas encontradas:\n")

    for m in medidas:
        print(f"{m['tabla']} | {m['medida']} = {m['dax']}\n")

    print(f"\nTotal medidas: {len(medidas)}")
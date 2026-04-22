"""Extraccion de medidas DAX desde archivos .tmdl."""

import os


def limpiar_dax(dax):
    """Clean DAX text by removing TMDL metadata fragments.

    Args:
        dax: Accumulated expression text extracted from TMDL.

    Returns:
        str: Cleaned DAX expression.
    """

    cortes = [
        "changedProperty",  # Inicio de bloque de propiedad modificada en TMDL
        "annotation",       # Inicio de anotaciones o metadatos del objeto
        "column ",          # Definicion de columna; no pertenece al DAX de medida
        "formatString",     # Propiedad de formato de visualizacion de la medida
        "dataType"          # Propiedad del tipo de dato de la medida
    ]

    # Cortar por el primer marcador que aparezca en el texto para evitar
    # recortes sucesivos dependientes del orden en la lista.
    posiciones = [dax.find(corte) for corte in cortes if dax.find(corte) != -1]
    if posiciones:
        dax = dax[:min(posiciones)]

    # Algunas extracciones dejan varios signos igual al inicio de la expresion.
    dax = dax.strip()

    while dax.startswith("="):
        dax = dax[1:].strip()

    return dax


def leer_medidas(ruta_pbix):
    """Extract measures and DAX expressions from table TMDL files.

    Args:
        ruta_pbix: Root path of the decomposed PBIX structure.

    Returns:
        list[dict]: Records with table, measure name, and DAX.

    Raises:
        FileNotFoundError: If Model/tables does not exist.
    """

    ruta_tablas = os.path.join(ruta_pbix, "Model", "tables")

    # Las medidas viven dentro de los .tmdl de cada tabla.
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

        # La expresion DAX puede ocupar varias lineas hasta cerrar el bloque.
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
                    # Se normaliza al final para evitar mezclar DAX con metadatos TMDL.
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


# Prueba local rapida
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(base_dir, "LN_IndicadoresRutasMIO")

    medidas = leer_medidas(ruta)

    print("\n📊 Medidas encontradas:\n")

    for m in medidas:
        print(f"{m['tabla']} | {m['medida']} = {m['dax']}\n")

    print(f"\nTotal medidas: {len(medidas)}")
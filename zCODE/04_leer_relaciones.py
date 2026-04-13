"""Extraccion de relaciones desde Model/relationships.tmdl."""

import os


def leer_relaciones(ruta_pbix):
    """
    Lee relaciones entre tablas desde relationships.tmdl.

    Parametros:
        ruta_pbix (str): Ruta raiz del PBIX descompuesto.

    Retorna:
        list[dict]: tabla_origen, columna_origen, tabla_destino y columna_destino.
    """

    ruta_rel = os.path.join(ruta_pbix, "Model", "relationships.tmdl")

    if not os.path.exists(ruta_rel):
        raise FileNotFoundError(f"No existe: {ruta_rel}")

    with open(ruta_rel, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()

    relaciones = []

    def limpiar_comillas(texto):
        texto = texto.strip()
        if texto.startswith("'") and texto.endswith("'") and len(texto) >= 2:
            return texto[1:-1]
        return texto

    def separar_referencia(ref):
        ref = ref.strip()

        if "[" in ref and ref.endswith("]"):
            tabla, columna = ref.split("[", 1)
            columna = columna[:-1]
            tabla = tabla.rstrip(".").strip()
        else:
            if "." not in ref:
                return ref, ""
            tabla, columna = ref.rsplit(".", 1)

        return limpiar_comillas(tabla), limpiar_comillas(columna)

    from_ref = None

    for linea in lineas:
        texto = linea.strip()

        if texto.startswith("fromColumn:"):
            from_ref = texto.split("fromColumn:", 1)[1].strip()

        elif texto.startswith("toColumn:") and from_ref:
            to_ref = texto.split("toColumn:", 1)[1].strip()

            origen_tabla, origen_col = separar_referencia(from_ref)
            destino_tabla, destino_col = separar_referencia(to_ref)

            relaciones.append({
                "tabla_origen": origen_tabla,
                "columna_origen": origen_col,
                "tabla_destino": destino_tabla,
                "columna_destino": destino_col
            })

            from_ref = None

    return relaciones


# Prueba local rapida
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(base_dir, "OFICINA_EVALUACION", "PBIXs_descompuestos", "LN_IndicadoresRutasMIO")

    relaciones = leer_relaciones(ruta)

    print("\n🔗 Relaciones encontradas:\n")

    for r in relaciones:
        print(f"{r['tabla_origen']}[{r['columna_origen']}] → {r['tabla_destino']}[{r['columna_destino']}]")

    print(f"\nTotal relaciones: {len(relaciones)}")
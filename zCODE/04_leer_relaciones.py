"""Extraccion de relaciones desde Model/relationships.tmdl."""

import os


def leer_relaciones(ruta_pbix):
    """Read table relationships from Model/relationships.tmdl.

    Args:
        ruta_pbix: Root path of the decomposed PBIX structure.

    Returns:
        list[dict]: Records with source and target table/column pairs.

    Raises:
        FileNotFoundError: If Model/relationships.tmdl does not exist.
    """

    ruta_rel = os.path.join(ruta_pbix, "Model", "relationships.tmdl")

    # Todas las relaciones del modelo se centralizan en este archivo.
    if not os.path.exists(ruta_rel):
        raise FileNotFoundError(f"No existe: {ruta_rel}")

    with open(ruta_rel, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()

    relaciones = []

    def limpiar_comillas(texto):
        """Remove wrapping single quotes from a TMDL identifier.

        Args:
            texto: Raw identifier text.

        Returns:
            str: Identifier without wrapping single quotes.
        """
        # TMDL puede envolver nombres con espacios entre comillas simples.
        texto = texto.strip()
        if texto.startswith("'") and texto.endswith("'") and len(texto) >= 2:
            return texto[1:-1]
        return texto

    def separar_referencia(ref):
        """Split a TMDL reference into table and column components.

        Args:
            ref: Raw reference in bracket or dot notation.

        Returns:
            tuple[str, str]: Parsed table and column names.
        """
        ref = ref.strip()

        if "[" in ref and ref.endswith("]"):
            # Soporta referencias tipo 'Tabla Nombre'[Columna].
            tabla, columna = ref.split("[", 1)
            columna = columna[:-1]
            tabla = tabla.rstrip(".").strip()
        else:
            if "." not in ref:
                return ref, ""
            # Soporta referencias tipo Tabla.Columna.
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
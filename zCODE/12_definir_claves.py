"""Infiere claves primarias y foraneas sobre entidades canonicas."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

AREA_ID_MANUAL = ""
AREA_ID_DEFAULT = "OFICINA_EVALUACION"
AREA_ID = (
    AREA_ID_MANUAL.strip()
    or os.getenv("PBIX_AREA", AREA_ID_DEFAULT).strip()
    or AREA_ID_DEFAULT
)

AREA_DIR = PROJECT_DIR / AREA_ID
OUTPUT_DIR = AREA_DIR / "PBIXs_output"
SILVER_DIR = OUTPUT_DIR / "silver"
ENTIDADES_DIR = SILVER_DIR / "entidades"
CLAVES_DIR = SILVER_DIR / "claves"


def log(mensaje: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {mensaje}")


def encontrar_ultimo_entidades() -> Path | None:
    if not ENTIDADES_DIR.exists():
        return None

    candidatos = sorted(ENTIDADES_DIR.glob("11_EntidadesCanonicas_*.xlsx"))
    if not candidatos:
        return None

    return max(candidatos, key=lambda p: p.stat().st_mtime)


def inferir_pk_por_entidad(atributos: pd.DataFrame) -> pd.DataFrame:
    resultado = []

    for entidad, grupo in atributos.groupby("entidad", dropna=False):
        g = grupo.copy()
        g["_prioridad"] = 3

        if "es_clave_candidata" in g.columns:
            g.loc[g["es_clave_candidata"] == True, "_prioridad"] = 1  # noqa: E712

        nombre_preferido_1 = f"id_{entidad}" if pd.notna(entidad) else None
        nombre_preferido_2 = f"{entidad}_id" if pd.notna(entidad) else None

        if nombre_preferido_1 is not None:
            g.loc[g["atributo"] == nombre_preferido_1, "_prioridad"] = 0
        if nombre_preferido_2 is not None:
            g.loc[g["atributo"] == nombre_preferido_2, "_prioridad"] = 0

        g = g.sort_values(by=["_prioridad", "atributo"], ascending=[True, True])
        pk = g.iloc[0]

        resultado.append(
            {
                "entidad": entidad,
                "pk_atributo": pk.get("atributo"),
                "pk_tipo_dato": pk.get("tipo_dato_canon"),
                "pk_confianza": "alta" if int(pk.get("_prioridad", 3)) <= 1 else "media",
            }
        )

    return pd.DataFrame(resultado)


def inferir_fk_desde_relaciones(relaciones: pd.DataFrame, pk_df: pd.DataFrame) -> pd.DataFrame:
    if relaciones.empty:
        return pd.DataFrame(columns=["entidad", "fk_atributo", "referencia_entidad", "referencia_pk", "fk_confianza"])

    pk_map = dict(zip(pk_df["entidad"], pk_df["pk_atributo"])) if not pk_df.empty else {}
    fks = []

    for _, row in relaciones.iterrows():
        entidad_hija = row.get("entidad_origen")
        atributo_hijo = row.get("atributo_origen")
        entidad_padre = row.get("entidad_destino")
        pk_padre = pk_map.get(entidad_padre)

        fks.append(
            {
                "entidad": entidad_hija,
                "fk_atributo": atributo_hijo,
                "referencia_entidad": entidad_padre,
                "referencia_pk": pk_padre,
                "fk_confianza": "alta" if pd.notna(pk_padre) else "media",
            }
        )

    return pd.DataFrame(fks).drop_duplicates().reset_index(drop=True)


def marcar_atributos(atributos: pd.DataFrame, pks: pd.DataFrame, fks: pd.DataFrame) -> pd.DataFrame:
    df = atributos.copy()
    df["es_pk"] = False
    df["es_fk"] = False

    pk_pairs = {(r.entidad, r.pk_atributo) for r in pks.itertuples(index=False)} if not pks.empty else set()
    fk_pairs = {(r.entidad, r.fk_atributo) for r in fks.itertuples(index=False)} if not fks.empty else set()

    df["es_pk"] = df.apply(lambda r: (r.get("entidad"), r.get("atributo")) in pk_pairs, axis=1)
    df["es_fk"] = df.apply(lambda r: (r.get("entidad"), r.get("atributo")) in fk_pairs, axis=1)

    return df


def exportar_salida(pks: pd.DataFrame, fks: pd.DataFrame, atributos_modelo: pd.DataFrame, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        pks.to_excel(writer, sheet_name="ClavesPrimarias", index=False)
        fks.to_excel(writer, sheet_name="ClavesForaneas", index=False)
        atributos_modelo.to_excel(writer, sheet_name="AtributosModelo", index=False)


def main() -> None:
    log(f"Iniciando definicion de claves para area {AREA_ID}...")

    entidades_file = encontrar_ultimo_entidades()
    if entidades_file is None:
        log("No se encontro salida del script 11. Ejecuta primero 11_entidades_canonicas.py")
        return

    log(f"Usando archivo: {entidades_file.name}")

    atributos = pd.read_excel(entidades_file, sheet_name="Atributos")
    relaciones = pd.read_excel(entidades_file, sheet_name="RelacionesCanon")

    pks = inferir_pk_por_entidad(atributos)
    fks = inferir_fk_desde_relaciones(relaciones, pks)
    atributos_modelo = marcar_atributos(atributos, pks, fks)

    output_file = CLAVES_DIR / (
        f"12_ClavesCanonicas_{AREA_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

    exportar_salida(pks, fks, atributos_modelo, output_file)

    log(f"Archivo generado: {output_file.name}")
    log(
        "Filas -> "
        f"PK: {len(pks)}, "
        f"FK: {len(fks)}, "
        f"AtributosModelo: {len(atributos_modelo)}"
    )


if __name__ == "__main__":
    main()

from pathlib import Path

import pandas as pd


def test_cargar_config_area_defaults(m06, tmp_path: Path):
    """Verify that default configuration is used when JSON is missing.

    Args:
        m06: Loaded module under test for PBIX orchestration.
        tmp_path: Temporary directory provided by pytest.
    """
    # Sin archivo JSON, la configuracion debe completarse con defaults del modulo.
    conf = m06.cargar_config_area(tmp_path / "no_existe.json")

    assert conf["area_id"]
    assert conf["paths"]["pbix_in"] == "PBIXs"


def test_cargar_config_area_override(m06, tmp_path: Path):
    """Verify that pipeline.json overrides only the values it defines.

    Args:
        m06: Loaded module under test for PBIX orchestration.
        tmp_path: Temporary directory provided by pytest.
    """
    # El archivo solo sobreescribe las claves presentes y deja el resto intacto.
    config = tmp_path / "pipeline.json"
    config.write_text(
        '{"area_id": "AREA_TEST", "paths": {"output": "salida_custom"}}',
        encoding="utf-8",
    )

    conf = m06.cargar_config_area(config)

    assert conf["area_id"] == "AREA_TEST"
    assert conf["paths"]["output"] == "salida_custom"


def test_resolver_ruta_area_relativa_y_absoluta(m06, tmp_path: Path):
    """Verify resolution of both relative and absolute area paths.

    Args:
        m06: Loaded module under test for PBIX orchestration.
        tmp_path: Temporary directory provided by pytest.
    """
    # Las rutas relativas se anclan al area; las absolutas se respetan tal cual.
    rel = m06.resolver_ruta_area(tmp_path, "PBIXs")
    abs_path = m06.resolver_ruta_area(tmp_path, str(tmp_path / "ABS"))

    assert rel == tmp_path / "PBIXs"
    assert abs_path == tmp_path / "ABS"


def test_metadata_corresponde_pbix(m06):
    """Verify that identical metadata matches the PBIX signature.

    Args:
        m06: Loaded module under test for PBIX orchestration.
    """
    # La comparacion debe aceptar una metadata identica a la firma del archivo.
    firma = {
        "pbix_name": "x.pbix",
        "pbix_path": "C:/tmp/x.pbix",
        "pbix_size": 10,
        "pbix_mtime_ns": 20,
    }

    assert m06.metadata_corresponde_pbix(dict(firma), firma)



def test_leer_y_guardar_metadata_extraccion(m06, tmp_path: Path, monkeypatch):
    """Verify that extraction metadata can be written and read back.

    Args:
        m06: Loaded module under test for PBIX orchestration.
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper for temporary attribute replacement.
    """
    # Se desactiva el log para aislar el comportamiento de persistencia.
    destino = tmp_path / "descomp"
    destino.mkdir(parents=True)

    firma = {
        "pbix_name": "a.pbix",
        "pbix_path": "C:/tmp/a.pbix",
        "pbix_size": 123,
        "pbix_mtime_ns": 456,
    }

    monkeypatch.setattr(m06, "log", lambda _: None)
    m06.guardar_metadata_extraccion(destino, firma)
    data = m06.leer_metadata_extraccion(destino)

    # La metadata debe conservar la firma y anadir la marca temporal de extraccion.
    assert data is not None
    assert data["pbix_name"] == "a.pbix"
    assert "extracted_at" in data


def test_descomponer_pbix_reutiliza_metadata(m06, tmp_path: Path, monkeypatch):
    """Verify that a current decomposition is reused without re-extraction.

    Args:
        m06: Loaded module under test for PBIX orchestration.
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper for temporary attribute replacement.
    """
    # Se simula una descomposicion ya existente y consistente con el PBIX actual.
    pbix = tmp_path / "reporte.pbix"
    pbix.write_bytes(b"x")

    descomp = tmp_path / "descomp"
    destino = descomp / "reporte"
    (destino / "Model" / "tables").mkdir(parents=True)

    monkeypatch.setattr(m06, "DESCOMP_DIR", descomp)
    monkeypatch.setattr(m06, "log", lambda _: None)

    firma = m06.construir_firma_pbix(pbix)
    m06.guardar_metadata_extraccion(destino, firma)

    resultado = m06.descomponer_pbix(pbix)

    assert resultado == destino


def test_procesar_pbix_ok(m06, tmp_path: Path, monkeypatch):
    """Verify the successful orchestration flow through final export.

    Args:
        m06: Loaded module under test for PBIX orchestration.
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper for temporary attribute replacement.
    """
    # Se reemplazan dependencias externas para probar solo la orquestacion.
    pbix = tmp_path / "ok.pbix"
    pbix.write_bytes(b"ok")

    ruta_descomp = tmp_path / "ok"
    (ruta_descomp / "Model" / "tables").mkdir(parents=True)

    monkeypatch.setattr(m06, "descomponer_pbix", lambda _: ruta_descomp)
    monkeypatch.setattr(m06, "PBIX_OUTPUT_DIR", tmp_path / "out")
    monkeypatch.setattr(m06, "log", lambda _: None)

    calls = {"export": False}

    def fake_exportar(tablas, columnas, medidas, relaciones, output_file):
        """Simulate export and validate that normalized structures are received.

        Args:
            tablas: DataFrame with table metadata.
            columnas: DataFrame with column metadata.
            medidas: DataFrame with measure metadata.
            relaciones: DataFrame with relationship metadata.
            output_file: Expected output workbook path.
        """
        calls["export"] = True
        assert isinstance(tablas, pd.DataFrame)
        assert output_file.name == "ok.xlsx"

    ok = m06.procesar_pbix(
        pbix,
        lambda ruta: ["Usos"],
        lambda ruta: [{"tabla": "Usos", "columna": "id", "tipo": "int64"}],
        lambda ruta: [{"tabla": "Usos", "medida": "Total", "dax": "SUM(Usos[id])"}],
        lambda ruta: [{"tabla_origen": "Usos", "columna_origen": "id", "tabla_destino": "Rutas", "columna_destino": "id"}],
        fake_exportar,
    )

    assert ok is True
    assert calls["export"] is True


def test_procesar_pbix_falla_si_no_hay_model(m06, tmp_path: Path, monkeypatch):
    """Verify that processing aborts when Model/tables is missing.

    Args:
        m06: Loaded module under test for PBIX orchestration.
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper for temporary attribute replacement.
    """
    # Si la descomposicion no contiene Model/tables, el proceso debe abortar limpio.
    pbix = tmp_path / "bad.pbix"
    pbix.write_bytes(b"bad")

    ruta_invalida = tmp_path / "sin_model"
    ruta_invalida.mkdir(parents=True)

    monkeypatch.setattr(m06, "descomponer_pbix", lambda _: ruta_invalida)
    monkeypatch.setattr(m06, "log", lambda _: None)

    ok = m06.procesar_pbix(
        pbix,
        lambda ruta: [],
        lambda ruta: [],
        lambda ruta: [],
        lambda ruta: [],
        lambda *args, **kwargs: None,
    )

    assert ok is False

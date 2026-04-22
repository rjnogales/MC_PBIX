from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ZCODE_DIR = Path(__file__).resolve().parents[1]


def load_script_module(filename: str, alias: str):
    """Load a zCODE script as an importable module for tests.

    Args:
        filename: Script filename inside the zCODE directory.
        alias: Module alias used during dynamic import.

    Returns:
        module: Imported Python module object.
    """
    script_path = ZCODE_DIR / filename
    spec = importlib.util.spec_from_file_location(alias, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def m01():
    """Provide the module under test for 01_leer_tablas.py."""
    return load_script_module("01_leer_tablas.py", "m01")


@pytest.fixture(scope="session")
def m02():
    """Provide the module under test for 02_leer_columnas.py."""
    return load_script_module("02_leer_columnas.py", "m02")


@pytest.fixture(scope="session")
def m03():
    """Provide the module under test for 03_leer_medidas.py."""
    return load_script_module("03_leer_medidas.py", "m03")


@pytest.fixture(scope="session")
def m04():
    """Provide the module under test for 04_leer_relaciones.py."""
    return load_script_module("04_leer_relaciones.py", "m04")


@pytest.fixture(scope="session")
def m05():
    """Provide the module under test for 05_exportar_excel.py."""
    return load_script_module("05_exportar_excel.py", "m05")


@pytest.fixture(scope="session")
def m06():
    """Provide the module under test for 06_procesar_pbixs.py."""
    return load_script_module("06_procesar_pbixs.py", "m06")


@pytest.fixture
def pbix_root(tmp_path: Path) -> Path:
    """Create a temporary root with the minimal decomposed PBIX structure.

    Args:
        tmp_path: Temporary directory managed by pytest.

    Returns:
        Path: Root path containing Model/tables.
    """
    root = tmp_path / "pbix"
    (root / "Model" / "tables").mkdir(parents=True)
    return root

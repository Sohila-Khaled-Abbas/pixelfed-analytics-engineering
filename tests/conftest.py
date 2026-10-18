"""Shared pytest fixtures for the PixelFed Analytics Engineering test suite."""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from schema_generator_core import parse_schema, SchemaContract, ColumnDef, TableDef  # noqa: E402
from generate_landing import build_table_format_map, FORMAT_GROUPS  # noqa: E402


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def schema_path(project_root: Path) -> Path:
    path = project_root / "schema.md"
    assert path.is_file(), f"schema.md not found at {path}"
    return path


@pytest.fixture(scope="session")
def parsed_schema(schema_path: Path) -> SchemaContract:
    return parse_schema(schema_path)


@pytest.fixture(scope="session")
def format_assignment(parsed_schema: SchemaSpec) -> dict[str, str]:
    return build_table_format_map(parsed_schema)

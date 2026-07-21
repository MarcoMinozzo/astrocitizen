from __future__ import annotations

import importlib

import pytest

from astrocitizen import CONTEXT_MODULES, __version__
from astrocitizen.ports import ArchivePort, CameraPort, SyncPort
from astrocitizen.shared import DomainError, new_id


def test_version() -> None:
    assert __version__ == "0.0.1"


@pytest.mark.parametrize("name", CONTEXT_MODULES)
def test_context_module_importable(name: str) -> None:
    mod = importlib.import_module(f"astrocitizen.{name}")
    assert mod.__doc__


def test_new_id_is_uuid4() -> None:
    value = new_id()
    assert value.version == 4


def test_domain_error_rule_id() -> None:
    err = DomainError("produto mínimo", rule_id="RN-080")
    assert err.rule_id == "RN-080"


def test_ports_exported() -> None:
    assert ArchivePort is not None
    assert CameraPort is not None
    assert SyncPort is not None

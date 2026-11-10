"""Smoke tests for the installed package layout."""

from importlib import import_module

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "adaptive_sequence_model",
        "adaptive_sequence_model.data",
        "adaptive_sequence_model.features",
        "adaptive_sequence_model.models",
        "adaptive_sequence_model.training",
        "adaptive_sequence_model.evaluation",
        "adaptive_sequence_model.portfolio",
        "adaptive_sequence_model.integrations",
    ],
)
def test_package_import(module):
    assert import_module(module).__name__ == module

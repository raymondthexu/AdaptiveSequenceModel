"""Configuration validation, snapshots, and CLI behavior."""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from adaptive_sequence_model.config import ConfigError, load_config, save_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def settings():
    return yaml.safe_load((ROOT / "configs/smoke.yaml").read_text())


def write_config(tmp_path, settings):
    path = tmp_path / "input.yaml"
    path.write_text(yaml.safe_dump(settings))
    return path


@pytest.mark.parametrize("name", ["base", "smoke"])
def test_examples(name):
    config = load_config(ROOT / f"configs/{name}.yaml")
    assert config.target.horizon == 1
    assert config.model.name == "linear"
    assert config.optimizer.learning_rate == 0.001
    assert config.split.train.end < config.split.validation.start


@pytest.mark.parametrize(
    ("section", "key", "value", "message"),
    [
        ("target", "horizon", 0, "target.horizon"),
        ("target", "horizon", -1, "greater than 0"),
        ("target", "horizon", True, "valid integer"),
        ("target", "horizon", "2", "valid integer"),
        ("features", "lookback", 0, "features.lookback"),
        ("features", "columns", [], "at least one column"),
        ("features", "columns", ["close", "close"], "no duplicates"),
        ("model", "name", "unknown", "model.name"),
        ("model", "hidden_size", 0, "model.hidden_size"),
        ("model", "dropout", 1.0, "model.dropout"),
        ("optimizer", "learning_rate", 0.0, "optimizer.learning_rate"),
        ("optimizer", "learning_rate", float("nan"), "finite number"),
        ("evaluation", "metrics", ["sharpe"], "evaluation.metrics"),
        ("evaluation", "metrics", [], "at least one metric"),
        ("dataset", "typo", "secret-value", "Extra inputs are not permitted"),
    ],
)
def test_invalid_settings(tmp_path, settings, section, key, value, message):
    settings.setdefault(section, {})[key] = value
    with pytest.raises(ConfigError, match=message) as caught:
        load_config(write_config(tmp_path, settings))
    assert "secret-value" not in str(caught.value)


@pytest.mark.parametrize(
    "value", ["/private/data.csv", "../data.csv", "${DATA}/x", "~/x", "C:\\data.csv"]
)
@pytest.mark.parametrize("field", ["dataset", "output_dir"])
def test_nonportable_paths(tmp_path, settings, value, field):
    if field == "dataset":
        settings["dataset"]["path"] = value
    else:
        settings[field] = value
    with pytest.raises(ConfigError, match="environment-relative path"):
        load_config(write_config(tmp_path, settings))


@pytest.mark.parametrize(
    ("period", "field", "value", "message"),
    [
        ("train", "start", "2024-02-30", "valid ISO date"),
        ("train", "start", "01/01/2024", "valid ISO date"),
        ("train", "start", "2025-01-01", "start must be on or before end"),
        ("train", "end", "2024-01-16", "train and validation.*overlap"),
        ("test", "start", "2024-01-23", "validation and test.*overlap"),
    ],
)
def test_invalid_splits(tmp_path, settings, period, field, value, message):
    settings["split"][period][field] = value
    with pytest.raises(ConfigError, match=message):
        load_config(write_config(tmp_path, settings))


def test_reversed_periods(tmp_path, settings):
    split = settings["split"]
    split["train"], split["test"] = split["test"], split["train"]
    with pytest.raises(ConfigError, match="out of order"):
        load_config(write_config(tmp_path, settings))


@pytest.mark.parametrize(
    "content",
    ["", "[]", "split: [", "seed: 0\nseed: 1", "seed: !!python/object:foo {}"],
)
def test_invalid_yaml(tmp_path, content):
    path = tmp_path / "invalid.yaml"
    path.write_text(content)
    with pytest.raises(ConfigError):
        load_config(path)


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="could not read"):
        load_config(tmp_path / "missing.yaml")


def test_unknown_top_level_key(tmp_path, settings):
    settings["api_token"] = "do-not-serialize-this-secret"
    with pytest.raises(ConfigError, match="api_token") as caught:
        load_config(write_config(tmp_path, settings))
    assert "do-not-serialize-this-secret" not in str(caught.value)


def test_snapshot_round_trip(tmp_path, monkeypatch):
    config = load_config(ROOT / "configs/smoke.yaml")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("API_TOKEN", "do-not-serialize-this-secret")
    destination = save_config(config)
    assert destination == Path("artifacts/smoke/config.yaml")
    assert load_config(destination) == config
    saved = destination.read_text()
    assert "learning_rate:" in saved
    assert "do-not-serialize-this-secret" not in saved
    assert str(tmp_path) not in saved


@pytest.mark.parametrize(
    "namespace", ["adaptive_sequence_model", "adaptive_sequence_lab"]
)
def test_cli_success_and_snapshot(tmp_path, namespace):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            f"{namespace}.validate_config",
            str(ROOT / "configs/smoke.yaml"),
            "--save",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "artifacts/smoke/config.yaml").is_file()


def test_cli_failure(tmp_path, settings):
    settings["target"] = {"horizon": 0}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "adaptive_sequence_lab.validate_config",
            str(write_config(tmp_path, settings)),
            "--save",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "target.horizon" in result.stderr
    assert not (tmp_path / "artifacts").exists()

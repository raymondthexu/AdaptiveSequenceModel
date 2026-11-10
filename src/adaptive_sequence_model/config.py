"""Typed, strict experiment configuration and portable snapshots."""

from __future__ import annotations

from datetime import date
from pathlib import Path, PureWindowsPath
from typing import Annotated, Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

PositiveInt = Annotated[int, Field(gt=0)]
Name = Annotated[str, Field(pattern=r"^[A-Za-z_][A-Za-z0-9_.-]*$")]


class ConfigError(ValueError):
    """A configuration could not be read, validated, or saved."""


class Schema(BaseModel):
    """Reject typos and implicit scalar coercion throughout the schema."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


def relative_path(value: str) -> str:
    """Keep paths portable without resolving or expanding environment values."""
    path = Path(value)
    windows = PureWindowsPath(value)
    if (
        not value.strip()
        or path.is_absolute()
        or windows.drive
        or windows.root
        or ".." in path.parts
        or ".." in windows.parts
        or any(char in value for char in ("$", "~", ":", "\\"))
    ):
        raise ValueError(
            "must be an environment-relative path without expansion or '..'"
        )
    return value


class DatasetConfig(Schema):
    path: str = "data/research.csv"
    format: Literal["csv", "parquet"] = "csv"
    date_column: Name = "date"

    _path = field_validator("path")(relative_path)


class TargetConfig(Schema):
    column: Name = "close"
    horizon: PositiveInt = 1


class FeaturesConfig(Schema):
    columns: tuple[Name, ...] = ("close",)
    lookback: PositiveInt = 20

    @field_validator("columns", mode="before")
    @classmethod
    def sequence(cls, value):
        return tuple(value) if isinstance(value, list) else value

    @field_validator("columns")
    @classmethod
    def unique_columns(cls, value):
        if not value or len(set(value)) != len(value):
            raise ValueError("must contain at least one column and no duplicates")
        return value


class DateRange(Schema):
    start: date
    end: date

    @field_validator("start", "end", mode="before")
    @classmethod
    def iso_date(cls, value):
        if type(value) is date:
            return value
        if isinstance(value, str):
            try:
                parsed = date.fromisoformat(value)
                if parsed.isoformat() == value:
                    return parsed
            except ValueError:
                pass
        raise ValueError("must be a valid ISO date (YYYY-MM-DD)")

    @model_validator(mode="after")
    def chronological(self):
        if self.start > self.end:
            raise ValueError("start must be on or before end")
        return self


class SplitConfig(Schema):
    train: DateRange
    validation: DateRange
    test: DateRange

    @model_validator(mode="after")
    def ordered_ranges(self):
        for earlier, later in (("train", "validation"), ("validation", "test")):
            if getattr(self, earlier).end >= getattr(self, later).start:
                raise ValueError(
                    f"{earlier} and {later} date ranges overlap or are out of order; "
                    f"{earlier}.end must be before {later}.start"
                )
        return self


class ModelConfig(Schema):
    # Configuration names reserve extension points; no model is implemented here.
    name: Literal["linear", "lstm", "transformer"] = "linear"
    hidden_size: PositiveInt = 64
    num_layers: PositiveInt = 1
    dropout: Annotated[float, Field(ge=0, lt=1)] = 0.0


class OptimizerConfig(Schema):
    name: Literal["adam", "adamw", "sgd"] = "adam"
    learning_rate: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 0.001
    weight_decay: Annotated[float, Field(ge=0, allow_inf_nan=False)] = 0.0


class EvaluationConfig(Schema):
    metrics: tuple[Literal["mse", "mae", "rmse"], ...] = ("mse", "mae")

    @field_validator("metrics", mode="before")
    @classmethod
    def sequence(cls, value):
        return tuple(value) if isinstance(value, list) else value

    @field_validator("metrics")
    @classmethod
    def unique_metrics(cls, value):
        if not value or len(set(value)) != len(value):
            raise ValueError("must contain at least one metric and no duplicates")
        return value


class ExperimentConfig(Schema):
    seed: Annotated[int, Field(ge=0)] = 0
    output_dir: str = "artifacts/experiment"
    dataset: DatasetConfig = Field(default_factory=DatasetConfig)
    target: TargetConfig = Field(default_factory=TargetConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    split: SplitConfig
    model: ModelConfig = Field(default_factory=ModelConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)

    _output_dir = field_validator("output_dir")(relative_path)


class _UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys rather than silently replacing settings."""

    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                if key in mapping:
                    raise ConfigError("duplicate YAML key")
                mapping[key] = self.construct_object(value_node, deep=deep)
            except TypeError as exc:
                raise ConfigError("YAML keys must be scalar values") from exc
        return mapping


def load_config(path: str | Path) -> ExperimentConfig:
    """Load a YAML file, apply defaults, and validate every section."""
    try:
        with Path(path).open(encoding="utf-8") as stream:
            values = yaml.load(stream, Loader=_UniqueKeyLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        # Do not echo source lines, which might contain accidentally supplied secrets.
        raise ConfigError("could not read configuration as valid YAML") from exc
    if not isinstance(values, dict):
        raise ConfigError("configuration must be a YAML mapping")
    try:
        return ExperimentConfig.model_validate(values)
    except ValidationError as exc:
        messages = []
        for error in exc.errors(include_input=False, include_url=False):
            location = ".".join(str(part) for part in error["loc"])
            messages.append(f"{location}: {error['msg']}")
        raise ConfigError("invalid configuration:\n" + "\n".join(messages)) from exc


def save_config(config: ExperimentConfig) -> Path:
    """Save resolved public settings under output_dir, relative to the working dir."""
    destination = Path(config.output_dir) / "config.yaml"
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False),
            encoding="utf-8",
        )
    except OSError as exc:
        raise ConfigError("could not save resolved configuration") from exc
    return destination

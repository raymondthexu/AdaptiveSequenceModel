# Adaptive Sequence Model

A reusable Python package scaffold for sequence-model research. This repository
currently contains package boundaries and development tooling; it does not include
datasets, implemented models, training runs, or trading strategies.

Research only. No trading returns are promised. Results from future experiments
must not be interpreted as investment advice or a guarantee of future performance.

## Setup

Install Python 3.9 or newer and [uv](https://docs.astral.sh/uv/getting-started/installation/)
(CI uses uv 0.9.8), then run from a fresh clone:

```sh
git clone https://github.com/raymondthexu/AdaptiveSequenceModel.git
cd AdaptiveSequenceModel
uv sync --locked
uv run --locked python -c "import adaptive_sequence_model"
make test
```

`uv sync --locked` installs the package in editable mode and the development tools
into `.venv`, using the committed `uv.lock`. `make test` runs Ruff lint, formatting
checks, and pytest. CI runs the same command on every push and pull request with
Python 3.9 and 3.13. If Make is unavailable, run:

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

Install optional commit hooks with `uv run --locked pre-commit install`.
Run all hooks with `uv run --locked pre-commit run --all-files`.
Use `make format` to apply lint fixes and formatting. After intentional dependency
changes in `pyproject.toml`, regenerate `uv.lock` with `uv lock` and run `make test`.

## Package layout

All modules live under `src/adaptive_sequence_model/`:

| Package | Intended responsibility |
| --- | --- |
| `data` | Dataset loading and validation |
| `features` | Feature construction and transformations |
| `models` | Sequence model interfaces |
| `training` | Training orchestration |
| `evaluation` | Research metrics and evaluation |
| `portfolio` | Portfolio research |
| `integrations` | External system adapters |

These are extension points. Concrete interfaces should be introduced with
their implementations and tests as later research requirements become clear.

## Experiment configuration

`configs/base.yaml` lists all settings; `configs/smoke.yaml` is a minimal independent
example. Validate without reading datasets or running training:

```sh
uv run --locked python -m adaptive_sequence_lab.validate_config configs/smoke.yaml
uv run --locked python -m adaptive_sequence_model.validate_config configs/smoke.yaml --save
```

Both commands use the same parser. With the environment activated, the issue's
`python -m adaptive_sequence_lab.validate_config configs/smoke.yaml` command also
works. `--save` writes the resolved defaults and supplied settings to
`<output_dir>/config.yaml`; it replaces an existing snapshot at that location.
The Python API is `load_config(path)` and `save_config(config)` in
`adaptive_sequence_model.config`.

The schema covers dataset, target, features, split, model, optimizer, evaluation,
seed, and output directory. Unknown or duplicate keys are errors. Horizon,
lookback, and model dimensions must be positive integers; optimizer learning rate
must be positive and finite. Model names are `linear`, `lstm`, and `transformer`;
these reserve configuration names only, with no training implementation yet.
Evaluation metrics are `mse`, `mae`, and `rmse`.

Split dates use `YYYY-MM-DD` and inclusive endpoints. Train, validation, and test
must be disjoint and chronologically ordered. This checks configured periods;
future dataset code must also prevent target-horizon leakage across boundaries.
Dataset and output paths are relative to the working directory (run commands
from the repository root), with no home, environment-variable, absolute-path,
or parent-directory expansion. Dataset existence is not checked at this stage.

Configuration files and snapshots are public settings only. Credential fields
are unsupported and unknown fields are rejected; environment variables are never
expanded or captured. Keep credentials in external secret storage and never put
secrets in ordinary configuration values, including filenames or column names.

## Public/private boundary and licensing

Public files must contain only independently developed, cleared research code and
documentation. Keep employer or client names, restricted datasets, credentials,
proprietary strategies, and contract-covered code out of this repository. Store
private research inputs and outputs separately. `.gitignore` excludes common local
artifact paths, but every contribution still needs review for sensitive content.

Public licensing is pending a review of applicable contracts and intellectual
property rights by the repository owner. No open-source license is granted at
this stage. Do not add a public license or publish restricted material until that
review is complete.

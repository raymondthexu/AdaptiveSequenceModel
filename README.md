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

These are empty extension points. Concrete interfaces should be introduced with
their implementations and tests as later research requirements become clear.

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

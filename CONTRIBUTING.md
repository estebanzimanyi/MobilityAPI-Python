# Contributing to MobilityAPI

Thank you for considering a contribution to MobilityAPI. This document covers how to set up a development environment, run the tests, and the conventions we follow when filing issues and pull requests.

## Development setup

### Prerequisites

- **Python 3.10** or later
- **PostgreSQL** with the [MobilityDB](https://github.com/MobilityDB/MobilityDB) extension installed
- A working clone of this repository

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure the database connection

Edit `config.json` (or set the corresponding environment variables) to point at your local PostgreSQL + MobilityDB instance.

### Run the server

```bash
chmod +x run.sh
./run.sh
```

The server listens on `localhost:8080` by default.

## Running the tests

```bash
./run.sh --with-tests
```

The test runner ingests an AIS dataset before running the integration tests. Expect ~23 minutes on first run if the JSON data file is not yet cached, ~21 seconds on subsequent runs.

## Filing issues

Please use the issue templates under `.github/ISSUE_TEMPLATE/`:

- **Bug report** — for unexpected behaviour, errors, or test failures.
- **Feature request** — for new endpoints, OGC-compliance improvements, or integration with other backends.

Include the smallest reproducible example you can. For OGC-conformance issues, please reference the relevant section of the [OGC API – Moving Features Standard](https://docs.ogc.org/is/22-003r3/22-003r3.html).

## Pull requests

- Branch from `master`. Use a descriptive branch name (`fix/`, `feat/`, `refactor/` prefix is encouraged).
- Keep PRs focused — one logical change per PR.
- Use the PR template under `.github/PULL_REQUEST_TEMPLATE.md`.
- Verify tests pass locally before opening the PR.
- Reference any related issues with `Fixes #N` or `Refs #N` in the description.

## Code style

Python source follows [PEP 8](https://peps.python.org/pep-0008/). The CI runs `ruff check` on every PR — please run it locally before pushing:

```bash
pip install ruff
ruff check .
```

## Lineage

MobilityAPI builds on the foundation of [pg_mfserv](https://github.com/MobilityDB/pg_mfserv), an OGC API – Moving Features prototype authored at ULB in 2024. See [`AUTHORS.md`](AUTHORS.md) for the contributor history across both phases of the project.

## License

By contributing, you agree that your contributions will be licensed under the project's [PostgreSQL License](LICENSE.txt).

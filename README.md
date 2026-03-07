# threep-commons

Shared reusable runtime and utility library for the Threepwood PySide project family.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)

- [Library Usage](#library-usage)

- [Project Structure](#project-structure)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Legal Disclaimer](#legal-disclaimer)

## Features

<!-- TODO: List key capabilities as bullet points. -->

## Requirements

- **Python 3.13+**


## Installation

```bat
python scripts\windows\setup_env.py
```

Creates the local `.venv` by running `uv sync --locked` and falls back to `uv sync` when no lockfile is available yet.

Manual development alternative:

```bat
uv sync --group dev
```


## Library Usage

Import reusable modules directly from `threep_commons` and keep APIs organized by concern.

```python
from threep_commons import __version__
```


## Project Structure

```text
threep-commons/
|-- pyproject.toml
|-- uv.lock
|-- src/
|   `-- threep_commons/
|       |-- __init__.py
|       |-- __main__.py

|       `-- py.typed
|-- scripts/
|   |-- policy/
|   |   `-- check_standard.py
|   `-- windows/

|       |-- run_tests.py
|       `-- setup_env.py
|-- tests/
|   |-- __init__.py
|   |-- unit/
|   |   `-- __init__.py
|   `-- integration/

|       `-- __init__.py

`-- .pre-commit-config.yaml
```

## Development

```bat
hatch run test
hatch run test-cov
hatch run lint:check
hatch run lint:fmt
hatch run lint:types
hatch run lint:policy
hatch run lint:all
hatch build
```

## Troubleshooting

<!-- TODO: Document common issues and fixes. -->

---

<!-- legal-disclaimer:start -->
## Legal Disclaimer

THIS SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE," WITHOUT WARRANTIES OF ANY KIND, WHETHER EXPRESS, IMPLIED, STATUTORY, OR OTHERWISE, INCLUDING, WITHOUT LIMITATION, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, NON-INFRINGEMENT, ACCURACY, OR QUIET ENJOYMENT. TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE AUTHORS, CONTRIBUTORS, MAINTAINERS, DISTRIBUTORS, AND AFFILIATED PARTIES SHALL NOT BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES, OR FOR ANY LOSS OF DATA, PROFITS, GOODWILL, BUSINESS OPPORTUNITY, OR SERVICE INTERRUPTION, ARISING OUT OF OR RELATING TO THE USE OF, OR INABILITY TO USE, THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. THIS SOFTWARE HAS BEEN DEVELOPED, IN WHOLE OR IN PART, BY "INTELLIGENT TOOLS"; ACCORDINGLY, OUTPUTS MAY CONTAIN ERRORS OR OMISSIONS, AND YOU ASSUME FULL RESPONSIBILITY FOR INDEPENDENT VALIDATION, TESTING, LEGAL COMPLIANCE, AND SAFE OPERATION PRIOR TO ANY RELIANCE OR DEPLOYMENT.
<!-- legal-disclaimer:end -->

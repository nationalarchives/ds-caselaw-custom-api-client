import os

if os.getenv("PDOC_DYNAMIC_VERSION") == "1":
    from pathlib import Path

    import tomllib

    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        __version__ = tomllib.load(f)["tool"]["poetry"]["version"]
        __pip_version_string__ = f"~={__version__}"
        __poetry_version_string__ = f' = "^{__version__}"'

else:
    __pip_version_string__ = ""
    __poetry_version_string__ = ""

__doc__ = f"""

# Installation

Include the API client in your project using Pip or Poetry:

```bash
pip install ds-caselaw-marklogic-api-client
```

```bash
poetry add ds-caselaw-marklogic-api-client
```

or in your projects `requirements.txt` with:

```text
ds-caselaw-marklogic-api-client{__pip_version_string__}
```

or `pyproject.toml` for Poetry with:

```text
ds-caselaw-marklogic-api-client{__poetry_version_string__}
```

# Usage

## Initialising the client

Import the `MarklogicApiClient` class and instantiate with appropriate credentials:

```python

from caselawclient.Client import MarklogicApiClient

client = MarklogicApiClient(
    host="hostname",
    username="username",
    password="password",
    use_https=True,
)

```

"""

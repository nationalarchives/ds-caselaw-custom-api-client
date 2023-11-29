"""

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
ds-caselaw-marklogic-api-client~=12.0.0
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

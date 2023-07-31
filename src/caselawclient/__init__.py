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

## (Deprecated) Use in-library client instance

This library will automatically initialise an instance of the client. This functionality is deprecated, and will be
removed.

The client expects the following environment variables to be set or defined in a `.env` file:

```bash
MARKLOGIC_HOST
MARKLOGIC_USER
MARKLOGIC_PASSWORD
MARKLOGIC_USE_HTTPS # Optional, defaults to False
```

Then import `api_client` from `caselawclient.Client`:

```python
from caselawclient.Client import api_client
```

"""

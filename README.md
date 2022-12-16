# The National Archives: Find Case Law

This repository is part of the [Find Case Law](https://caselaw.nationalarchives.gov.uk/) project at [The National Archives](https://www.nationalarchives.gov.uk/). For more information on the project, check [the documentation](https://github.com/nationalarchives/ds-find-caselaw-docs).

# MarkLogic API Client

![PyPI](https://img.shields.io/pypi/v/ds-caselaw-marklogic-api-client) ![Libraries.io dependency status for latest release](https://img.shields.io/librariesio/release/pypi/ds-caselaw-marklogic-api-client)

This is an API Client for connecting to Marklogic for The National Archive's Caselaw site.

This package is published on PyPI: https://pypi.org/project/ds-caselaw-marklogic-api-client/

## Usage

Include the API client in your project using PIP:
```bash
pip install ds-caselaw-marklogic-api-client
```

or in your projects `requirements.txt` with:
```text
ds-caselaw-marklogic-api-client~=2.0.0
```

### Using the client

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

Alternatively, you can import the base class and instantiate it with different credentials:

```python
from caselawclient.Client import MarklogicApiClient

client = MarklogicApiClient(
    host="",
    username="",
    password="",
    use_https=False,
)
```

`Client` also exports some exception classes:
```python
MarklogicAPIError
MarklogicBadRequestError
MarklogicUnauthorizedError
MarklogicNotPermittedError
MarklogicResourceNotFoundError
MarklogicCommunicationError
```

### XML Tools
There is also a small set of xml helper tools that provide some common functionality for dealing with xml:

```python
from caselawclient import xml_tools

xml_tools.get_metadata_name_value(xml)
xml_tools.get_metadata_name_element(xml)
xml_tools.get_search_matches(element)
```

## Testing

To run the test suite:

```bash
pip install -r requirements.txt
python -m pytest
```

## Making changes

When making a change, update the [changelog](CHANGELOG.md) using the
[Keep a Changelog 1.0.0](https://keepachangelog.com/en/1.0.0/) format. Pull
requests should not be merged before any relevant updates are made.

## Releasing

When making a new release, update the [changelog](CHANGELOG.md) in the release
pull request.

The package will **only** be released to PyPI if the branch is tagged. A merge
to main alone will **not** trigger a release to PyPI.

To create a release:

0. Update the version number in `setup.cfg`
0. Create a branch `release/v{major}.{minor}.{patch}`
0. Update `CHANGELOG.md` for the release
0. Commit and push
0. Open a PR from that branch to main
0. Get approval on the PR
0. Merge the PR to main and push
0. Tag the merge commit on `main` with `v{major}.{minor}.{patch}` and push the tag
0. Create a release in [Github releases](https://github.com/nationalarchives/ds-caselaw-custom-api-client/releases)
using the created tag

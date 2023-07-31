# The National Archives: Find Case Law

This repository is part of the [Find Case Law](https://caselaw.nationalarchives.gov.uk/) project at [The National Archives](https://www.nationalarchives.gov.uk/). For more information on the project, check [the documentation](https://github.com/nationalarchives/ds-find-caselaw-docs).

# MarkLogic API Client

[![PyPI](https://img.shields.io/pypi/v/ds-caselaw-marklogic-api-client)](https://pypi.org/project/ds-caselaw-marklogic-api-client/) ![Libraries.io dependency status for latest release](https://img.shields.io/librariesio/release/pypi/ds-caselaw-marklogic-api-client)

This is an API Client for connecting to Marklogic for The National Archive's Caselaw site.

This package is published on PyPI: https://pypi.org/project/ds-caselaw-marklogic-api-client/

## Usage

You can find documentation of the client class and available methods [here](https://nationalarchives.github.io/ds-caselaw-custom-api-client).

## Testing

To run the test suite:

```bash
poetry install
poetry run pytest
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

0. Update the version number in `pyproject.toml`
0. Create a branch `release/v{major}.{minor}.{patch}`
0. Update `CHANGELOG.md` for the release
0. Commit and push
0. Open a PR from that branch to main
0. Get approval on the PR
0. Merge the PR to main and push
0. Tag the merge commit on `main` with `v{major}.{minor}.{patch}` and push the tag
0. Create a release in [Github releases](https://github.com/nationalarchives/ds-caselaw-custom-api-client/releases)
using the created tag

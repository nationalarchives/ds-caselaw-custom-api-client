# The National Archives: Find Case Law

This repository is part of the [Find Case Law](https://caselaw.nationalarchives.gov.uk/) project at [The National Archives](https://www.nationalarchives.gov.uk/). For more information on the project, check [the documentation](https://github.com/nationalarchives/ds-find-caselaw-docs).

# MarkLogic API Client

[![PyPI](https://img.shields.io/pypi/v/ds-caselaw-marklogic-api-client)](https://pypi.org/project/ds-caselaw-marklogic-api-client/)
![Libraries.io dependency status for latest release](https://img.shields.io/librariesio/release/pypi/ds-caselaw-marklogic-api-client)
![Code Coverage](https://img.shields.io/codecov/c/github/nationalarchives/ds-caselaw-custom-api-client)

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

MarkLogic integration tests live under `tests/marklogic/` and are **opt-in**: the default `poetry run pytest` excludes them (`-m 'not marklogic'`). They replace the old standalone `smoketest/` module and load a fixed corpus from `marklogic_harness/fixtures/documents/` (URIs under `test/…` as well as `smoketest/…`) so CI does not depend on staging.

CI runs them in a dedicated job against a local MarkLogic container (see `.github/workflows/test.yml`).

To run locally against Docker or another MarkLogic instance, set `MARKLOGIC_HOST`, `MARKLOGIC_USER`, and `MARKLOGIC_PASSWORD` in a `.env` file, then:

```bash
poetry run pytest -o addopts= -p marklogic_harness.pytest_plugin -m marklogic tests/marklogic
```

## Making changes

When making a change, update the [changelog](CHANGELOG.md) using the
[Keep a Changelog 1.0.0](https://keepachangelog.com/en/1.0.0/) format. Pull
requests should not be merged before any relevant updates are made.

## Deployment

<!-- last_review: 2026-04-13 -->

This repository will auto-deploy [documentation](https://nationalarchives.github.io/ds-caselaw-custom-api-client) to GitHub Pages when changes are made to `main`.

## Release process

<!-- last_review: 2026-04-13 -->

When making a new release, update the [changelog](CHANGELOG.md) in the release
pull request.

The package will **only** be released to PyPI if the branch is tagged. A merge
to main alone will **not** trigger a release to PyPI.

To create a release:

0. Update the version number in `pyproject.toml`
1. Create a branch `release/v{major}.{minor}.{patch}`
2. Update `CHANGELOG.md` for the release
3. Commit and push
4. Open a PR from that branch to main
5. Get approval on the PR
6. Merge the PR to main and push
7. Tag the merge commit on `main` with `v{major}.{minor}.{patch}` and push the tag
8. Create a release in [Github releases](https://github.com/nationalarchives/ds-caselaw-custom-api-client/releases)
   using the created tag

If the release fails to push to PyPI, you can delete the tag with `git pull`, `git push --delete origin v1.2.3` and try again.

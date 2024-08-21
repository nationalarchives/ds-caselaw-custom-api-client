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

There are also some smoketests in `smoketests.py` which run against a MarkLogic database but do not run in CI currently.

To run them locally you can set the environment variables as detailed in the file in a `.env` file or just hardcode them in, as long as you don't commit those changes to the repo.

And then run

```bash
poetry run pytest smoketest.py
```

To start with when running this, we have been choosing to point to the staging MarkLogic to have more confidence that the setup is a good representation of production as opposed to a local MarkLogic instance but that can work too.

Eventually we will make it so that we run these tests in CI and probably point to a dedicated testing MarkLogic instance so we don't get conflicts with people using staging for manual testing.

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

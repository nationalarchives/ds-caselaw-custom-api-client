# Caselaw Marklogic API Client

This is an API Client for connecting to Marklogic for The National Archive's Caselaw site.

This package is published on PyPI: https://pypi.org/project/ds-caselaw-marklogic-api-client/

## Making changes

When making a change, update the [changelog](CHANGELOG.md) using the
[Keep a Changelog 1.0.0](https://keepachangelog.com/en/1.0.0/) format. Pull
requests should not be merged before any relevant updates are made.

## Releasing changes

When making a new release, update the [changelog](CHANGELOG.md) in the release
pull request.

The package will **only** be released to PyPI if the branch is tagged. A merge 
to main alone will **not** trigger a release to PyPI.

To create a release:

0. Update the version number in `setup.cfg`
1. Create a branch release/xxx
2. Update changelog for the release
3. Commit and push
4. Open a PR from that branch to main
5. Get approval on the PR
6. Tag the HEAD of the PR release-xxx and push the tag
7. Merge the PR to main and push


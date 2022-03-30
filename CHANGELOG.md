# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.0.0].

## [Unreleased]

## [Release 2.1.2]
- Add a new anonymised content flag

## [Release 2.1.1]
- Fix intermittently failing XSLT transforms

## [Release 2.1.0]
- Refactor save_judgment_xml to use the eval endpoint, so that we can introduce versioning via na XQuery.
- List all versions of a managed judgment
- Get a version of a managed judgment
- Restrict search to managed judgments only
- Set properties on a judgment using the dls namespace, not xdmp
- Insert & manage a new document
- Check in and check out a document for editing
- Use document properties on the "original" version of the judgment, not its version, to see if a judgment is published

## [Release 2.0.1]
- Minor bugfixes

## [Release 2.0.0]
- Refactored property accessor methods
- BREAKING CHANGE `is_document_published` changed to `get_published` and `publish_document` changed to `set_published`.

## [Release 1.0.5]
- Initial tagged release

[unreleased]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/relese-2.1.2...HEAD
[Release 2.1.2]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-2.1.1...release-2.1.2
[Release 2.1.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-2.1.0...release-2.1.1
[Release 2.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-2.0.1...release-2.1.0
[release 2.0.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-2.0.0...release-2.0.1
[release 2.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-1.0.5...release-2.0.0
[release 1.0.5]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/releases/tag/release-1.0.5
[keep a changelog 1.0.0]: https://keepachangelog.com/en/1.0.0/
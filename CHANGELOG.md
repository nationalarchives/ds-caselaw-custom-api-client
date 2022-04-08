# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.0.0].

## [Unreleased]
- Parameterize the location of images in the XSLT transformation
- Use the `invoke` endpoint, and the `search.xqy` stored on Marklogic, to search

## [Release 3.2.0]
- Add flag to advanced_search to enable filtering out published documents from the search

## [Release 3.1.0]
- Add function to get and set text properties on a document

## [Release 3.0.1]
- Fix insert_document xquery to call the document-insert-and-manage function

## [Release 3.0.0]
- Replace LXML with standard library xml for wider compatibility and reduced build times

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

[unreleased]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-3.2.0...HEAD
[Release 3.2.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-3.1.1..release-3.2.0
[Release 3.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-3.0.1..release-3.1.0
[Release 3.0.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-3.0.0..release-3.0.1
[Release 3.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-2.1.2...release-3.0.0
[Release 2.1.2]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-2.1.1...release-2.1.2
[Release 2.1.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-2.1.0...release-2.1.1
[Release 2.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-2.0.1...release-2.1.0
[release 2.0.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-2.0.0...release-2.0.1
[release 2.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-1.0.5...release-2.0.0
[release 1.0.5]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/releases/tag/release-1.0.5
[keep a changelog 1.0.0]: https://keepachangelog.com/en/1.0.0/
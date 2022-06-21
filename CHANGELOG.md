# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.0.0].

## [Unreleased]

## [Release 4.6.0]
- Allow the xsl filename used in the judgment transformation to vary. We have two xsls available in Marklogic -
  `judgment2` (the accessible version) and `judgment0` (the "as handed down" version). Add two helper methods
  `accessible_judgment_transformation()` and `original_judgment_transformation()` to call these transformations without
  specifying the xsl filename.
- Copy judgment from URI to URI

## [Release 4.5.4]
- Adds a new `delete_judgment` endpoint, for deleting a judgment from marklogic

## [Release 4.5.3]
- Create a new `akn:FRBRdate`, `uk:cite` and `uk:court` nodes for the judgment metadata, if they do not exist

## [Release 4.5.2]
- Create a new `akn:FRBRname` node for the judgment metadata name, if one does not exist

## [Release 4.5.1]
- Patch release to update `setup.cfg`, which was missed from v4.5.0

## [Release 4.5.0]
- Allow metadata elements (name, date, court and citation) to be edited in the XML via XQuery, not by deserialising and
  serialising the XML in the implementing client code.

## [Release 4.4.0]
- If an element doesn't exist in a document, `xml_tools.get_element` tries to return an empty element with the same
  name as the desired element.

## [Release 4.3.0]
- Add function to retrieve the last time a document or it's properties was updated

## [Release 4.2.0]
- Add neutral citation and specific keyword search parameters to advanced search

## [Release 4.1.0]
- Use error code from eval response body to throw MarklogicResourceNotFound errors

## [Release 4.0.0]
- Parameterize the location of images in the XSLT transformation
- Use the `invoke` endpoint, and the `search.xqy` stored on Marklogic, to search
- Remove the `database` parameter in `eval`, it's not required; the db associated with the REST server is used

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

[Unreleased]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.6.0...HEAD
[Release 4.6.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.6.0...4.5.4
[Release 4.5.4]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.5.4...4.5.3
[Release 4.5.3]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.5.3...4.5.2
[Release 4.5.2]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.5.2...4.5.1
[Release 4.5.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.5.1...4.5.0
[Release 4.5.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.5.0...4.4.0
[Release 4.4.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.4.0...4.3.0
[Release 4.3.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.3.0...4.2.0
[Release 4.2.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.2.0...4.1.0
[Release 4.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.1.0...4.0.0
[Release 4.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/release-4.0.0...3.2.0
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

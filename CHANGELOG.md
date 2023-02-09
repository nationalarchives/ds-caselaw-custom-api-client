# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.0.0].

## [Release 5.2.3]
- Add content hash validation when we save a locked judgment

## [Release 5.2.2]
- Bug fix: setting court was not valid XQuery in eval context

## [Release 5.2.1]
- Improvements to code linting
- Expose hash of judgment content
- Unset the court tag where the court is an empty string

## [Release 5.2.0]
- Clarify release process documentation
- Add pypi version badge and libraries.io dependency shield
- Expose MarklogicValidationFailed exception

## [Release 5.1.4]
- Validate against a schema when priv API document is uploaded
- Add CodeQL configuration
- Add a check for secrets
- Bump certifi from 2021.10.8 to 2022.12.7

## [Release 5.1.3]
- Don't crash if multipart data is actually an empty bytestring.

## [Release 5.1.2]
** This release had a bug where the Editor UI was unusable. **
- Ensure Work Date and Court values are returned as text

## [Release 5.1.1]
- Get properties for a range of URIs for use in search results

## [Release 5.1.0]
- Remove a debug `print()` statement that was missed
- Admin users can't read unpublished judgments
- Deprecate XMLTools methods
- Fix `TypeError: 'type' object is not subscriptable`

## [Release 5.0.0]
- Breaking change: passes a list of zero-or-more courts, rather than a string that might be empty.
- Search queries: pages less than one are treated as one

## [Release 4.10.0]
- Add linting
- Ensure only people who are allowed to view unpublished judgments can view them
- Refactor tests
- Break judgment checkout
- Methods & XQueries to get & set all metadata
- DRY up some aspects of the API Client
- Support renaming of the XSL Transformation files
- Speed up privilege checking

## [Release 4.9.2]
- Add user_has_privilege method & XQuery to check if a user has a privilege
- Use `user_has_privilege` to check if a user can see unpublished documents
- Move error message codes and messages into this client
- New errors handled from Marklogic
- New function to save XML for a locked judgment

## [Release 4.9.1]
- Fix: add external declaration to XQuery parameter
- Bump version of requests to 2.28.1
- Raise error if unpublished document is not returned
- Use -1 as value meaning 'lock forever' in checkout_judgment
- Return none if the judgment is not locked, rather than an empty string

## [Release 4.9.0]
- Add optional annotation parameter to `checkout_judgment` method
- Add method to get the lock/checkout status of a judgment
- Judgment checkout may optionally expire at midnight

## [Release 4.8.0]
- Gracefully handle a null, empty or unexpected error response from Marklogic
- Rename set_judgment_date to set_judgment_work_expression_date
- Update the FRBRWork and FRBRExpression dates and @name attributes

## [Release 4.7.1]
- Fix a typo in setting the internal URI of a judgment

## [Release 4.7.0]
- Change the XQuery delete method from xdmp:document-delete to dls:document-delete
- Change the behaviour of 'last-modified' dates to use prop:last-modified rather than xdmp:document-timestamp
- Set the judgment's internal URI (`FRBRthis` and `FRBRuri` nodes)

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

[Unreleased]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.2.3...HEAD
[Release 5.2.2]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.2.2...v5.2.3
[Release 5.2.2]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.2.1...v5.2.2
[Release 5.2.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.2.0...v5.2.1
[Release 5.2.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.1.4...v5.2.0
[Release 5.1.4]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.1.3...v5.1.4
[Release 5.1.3]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.1.2...v5.1.3
[Release 5.1.2]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.1.1...v5.1.2
[Release 5.1.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.1.0...v5.1.1
[Release 5.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.0.0...v5.1.0
[Release 5.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.10.0...v5.0.0
[Release 4.10.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.9.2...v4.10.0
[Release 4.9.2]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.9.1...v4.9.2
[Release 4.9.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.9.0...v4.9.1
[Release 4.9.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.8.0...v4.9.0
[Release 4.8.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.7.1...v4.8.0
[Release 4.7.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.7.0...v4.7.1
[Release 4.7.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.6.0...v4.7.0
[Release 4.6.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.5.4...v4.6.0
[Release 4.5.4]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.5.3...v4.5.4
[Release 4.5.3]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.5.2...v4.5.3
[Release 4.5.2]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.5.1...v4.5.2
[Release 4.5.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.5.0...v4.5.1
[Release 4.5.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.4.0...v4.5.0
[Release 4.4.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.3.0...v4.4.0
[Release 4.3.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.2.0...v4.3.0
[Release 4.2.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.1.0...v4.2.0
[Release 4.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v4.0.0...v4.1.0
[Release 4.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v3.2.0...v4.0.0
[Release 3.2.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v3.1.1...v3.2.0
[Release 3.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v3.0.1...v3.1.0
[Release 3.0.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v3.0.0...v3.0.1
[Release 3.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v2.1.2...v3.0.0
[Release 2.1.2]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v2.1.1...v2.1.2
[Release 2.1.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v2.1.0...v2.1.1
[Release 2.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v2.0.1...v2.1.0
[Release 2.0.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v2.0.0...v2.0.1
[Release 2.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v1.0.5...v2.0.0
[Release 1.0.5]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/releases/tag/v1.0.5
[keep a changelog 1.0.0]: https://keepachangelog.com/en/1.0.0/

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.0.0].

## [Unreleased]

- New versions of a document created with `insert_document_xml` can now be annotated
- BREAKING: Renamed `save_judgment_xml` to `update_document_xml`

## [Release 15.1.2
- Expose the creation date of a version

## [Release 15.1.1]
- Get version annotation for a single document
- Expose the type of the latest manifestation date of a document

## [Release 15.1.0]

- Search results for press summaries now include NCNs
- Search results now correctly include document status information
- Latest manifestation datetime is available for documents (including versions)

## [Release 15.0.1]
- Bugfix: document_date_as_date shouldn't fail hard if we can't parse it.

## [Release 15.0.0]

- Changed `is_failure` to rely on `failed_to_parse`, rather than `failure` in the URI.

- Added `transformation_datetime` to `Document`
- Added `enrichment_datetime` to `Document`
- Added `get_manifestation_datetimes` to `Document`
- Added `get_latest_manifestation_datetime` to `Document`
- Added `versions_as_documents` to `Document`
- Added `is_version` to `Document`
- Added `version_number` to `Document`

## [Release 14.1.0]

- Add default user agent string
- Add functions for overwriting and moving judgments

## [Release 14.0.2]

- Fixed `neutral_citation` property to look within `preface` tag rather than `mainBody` for press summaries, due to updated parsing resulting in updated press summary xml structure.
- Added `python-dotenv` as a poetry `dev` dependency to be able to run the new `smoketest.py` file that connects to a MarkLogic instance.

## [Release 14.0.1]

- Fixed `Client.set_document_court` method
- Fixed `Client.get_document_type_from_uri` method

## [Release 14.0.0]

- **Breaking:**: Removed `document.is_editable` in favour of the more descriptive and better-tested `document.failed_to_parse`.
- Add new `Document.delete()` method.
- Generalised the set judgment metadata methods to set document metadata methods specifically for name, court and date.

## [Release 13.2.1]
 - Fix issues blocking push to PyPI

## [Release 13.2.0]
 - Add a "Best human identifier" to Documents

## [Release 13.1.0]

- Added `get_judgment_xml_bytestring` and `content_as_xml_bytestring` to `Client`
- Fixed `content_as_xml_tree` by making it use `content_as_xml_bytestring`
- Made `Document` class' `name`, `court`, `document_date_as_string` and `document_date_as_date` work for Press Summaries also.
- Added `neutral_citation` property and validation to `PressSummary` class.
- Significant improvements to inline documentation of the code.
- **Deprecated**: The `caselawclient.api_client` instance should be considered deprecated. Projects should instead initialise their own instance.

## [Release 13.0.0]

### Breaking changes

- supplemental/anonymous/sensitive getters/setters removed
- XQueries which return multiple responses will raise an error


- Refactored `Document` class' `name`, `court`, `document_date_as_string` and `document_date_as_date` (previously judgment_date_...) on Document class and neutral_citation on Judgment class making use of the new cached `content_as_xml_tree` property.
- Renamed `judgment_date_as_string` `judgment_date_as_date` to `document_date_as_string` and `document_date_as_date` respectively.
- Added `content_as_xml_tree` cached property to `Document` class
- Changed the `Document` class' `content_as_xml` to be a cached_property also. [Note: this changelog line previously mistakenly referred to `content_as_html`.]
- Removed `get_judgment_name`, `get_judgment_citation`, `get_judgment_court`, `get_judgment_work_date` from the `Client` class and associated `.xqy` files.
- Add a new `MarklogicApiClient.get_document_by_uri` method to retrieve a document (of any type) by URI.
- New `get_document_by_uri` method on API client returning unique types for `Judgment`s and `PressSummary`s.
- New `Document.enrich()` method to trigger enrichment

## [Release 12.0.0]

- **Breaking**: Renamed `Judgment` to `Document`
- **Breaking**: `Document.judgment_exists` is now `Document.document_exists`

## [Release 11.0.1]

- Check for a valid court, rather than an present one
- Trim whitespace when trying to set an NCN
## [Release 11.0.0]

- **Breaking**: Renamed `copy_judgment` to `copy_document`
- `copy_document` now adds the document to the appropriate collection based on the uri.

## [Release 10.1.0]

- `Judgment.validation_failure_messages` method for retrieving a list of strings with reasons a judgment cannot be published.

## [Release 10.0.1]
- Fixed `insert_document_xml` to pattern match uris with and add documents to `press-summary`, not `press_summary`.

## [Release 10.0.0]
- **BREAKING**: Renamed `insert_judgment_xml` to `insert_document_xml` and enhanced it to place a document in the appropriate collection (`press_summary` or `judgment`)

## [Release 9.0.0]
- **BREAKING**: Changed `SearchParameters` dataclass field from `q` to `query`
- Added `search_helpers` module to allow clients to search and process document search responses in one go.

## [Release 8.0.0]
- Added `SearchParameters` dataclass for use with search functions using the legacy kwargs from `Client.advanced_search` and new `collections` field for filtering by collections
- **BREAKING**: Changed `Client.advanced_search` interface to take in `SearchParameters` as opposed to the legacy kwargs.
- Added `search_and_decode_response` and `search_judgments_and_decode_response` methods to `Client`
- Added `SearchResponse`, `SearchResult`, `SearchResultMetadata` classes to encapsulate and process document search responses.

## [Release 7.0.0]
- **BREAKING**: Instantiating a`Judgment` object will now raise a `caselawclient.errors.JudgmentNotFoundError` if the uri passed in does not correspond to a valid Judgment, rather than attempting (and failing) to return a `MarklogicResourceNotFoundError`
- Added `judgment_exists` method to `Client` class
- Make version_uri optional in Judgment.content_as_html
- Ensure XSLT_IMAGE_LOCATION existing doesn't break tests
- Improve detection of when a judgment doesn't exist
- Unlock judgment on Judgment.unpublish() so editors can unpublish immediately after a publish

## [Release 6.1.0]
- `Judgment.publish` method will now reject publication in more invalid states (must have a name, must have a valid NCN, must have a court code).
- Less strict version pinning of dependencies to give downstream package users more flexibility in resolving.

## [Release 6.0.0]
- Significantly more type annotations on `Client` and `Judgment` methods, including some which are stricter than before.
  This is potentially a *breaking change* if implementations have been relying on duck typing.
- Automatic generation of strict typing for XQuery files which run against MarkLogic.
- Improvements to the methods used in content hashing, which will be breaking changes if these are used downstream.

## [Release 5.3.2]
- Correct import location used in Judgment model, so it's usable when packaged

## [Release 5.3.1]
- Fix broken build process

## [Release 5.3.0] (Yanked)
- Dependabot now updates dependencies for all new versions, not just security updates
- Use Poetry for dependency management, to improve robustness
- Add a `Judgment` class (copied from Editor Interface) to begin the process of harmonising how various services interface with the data

## [Release 5.2.6]
- Add code coverage reporting to CI
- Make a PEP-561 declaration of typing

## [Release 5.2.5]
- Re-add the code that was pointing the XSLT to the assets

## [Release 5.2.4]
- This release had a bug, fixed by 5.2.5
- HTML view: Do not default to current version if the version doesn't exist (cause an error instead)

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

[Unreleased]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v15.1.2...HEAD
[Release 15.1.2]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v15.1.1...v15.1.2
[Release 15.1.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v15.1.0...v15.1.1
[Release 15.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v15.0.1...v15.1.0
[Release 15.0.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v15.0.0...v15.0.1
[Release 15.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v14.1.0...v15.0.0
[Release 14.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v14.0.2...v14.1.0
[Release 14.0.2]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v14.0.1...v14.0.2
[Release 14.0.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v14.0.0...v14.0.1
[Release 14.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v13.2.1...v14.0.0
[Release 13.2.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v13.2.0...v13.2.1
[Release 13.2.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v13.0.0...v13.2.0
[Release 13.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v13.0.0...v13.1.0
[Release 13.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v12.0.0...v13.0.0
[Release 12.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v11.0.1...v12.0.0
[Release 11.0.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v11.0.0...v11.0.1
[Release 11.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v10.1.0...v11.0.0
[Release 10.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v10.0.1...v10.1.0
[Release 10.0.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v10.0.0...v10.0.1
[Release 10.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v9.0.0...v10.0.0
[Release 9.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v8.0.0...v9.0.0
[Release 8.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v7.0.0...v8.0.0
[Release 7.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v6.1.0...v7.0.0
[Release 6.1.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v6.0.0...v6.1.0
[Release 6.0.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.3.2...v6.0.0
[Release 5.3.1]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.3.1...v5.3.2
[Release 5.3.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.3.0...v5.3.1
[Release 5.3.0]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.2.6...v5.3.0
[Release 5.2.6]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.2.5...v5.2.6
[Release 5.2.5]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.2.4...v5.2.5
[Release 5.2.4]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.2.3...v5.2.4
[Release 5.2.3]: https://github.com/nationalarchives/ds-caselaw-custom-api-client/compare/v5.2.2...v5.2.3
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

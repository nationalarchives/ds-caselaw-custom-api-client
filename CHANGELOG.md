# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.0.0].

## v44.0.1 (2025-11-26)

### Fix

- Ensure default XML document for tests has content in the header so has_content returns true still

## v44.0.0 (2025-11-26)

### Breaking change

- Remove recursive numbering of `<uk:mark>` tags for performance reasons. Use JS instead.

### Feat

- Only check header when working out if something `has_content`

## Unreleased

### Feat

- **MarklogicApiClient**: add new method to get total number of documents awaiting reparse

### Fix

- **deps**: update dependency certifi to >=2025.11.12,<2025.12.0

## v43.1.0 (2025-11-05)

### Feat

- Detect unpublished uncleaned assets

## v43.0.0 (2025-11-04)

### BREAKING CHANGE

- VersionAnnotation is now located at models.documents.versions, and not client_helpers as previously.

### Feat

- **types** SuccessFailureMessageTuple can now be used as a boolean value
- **Document**: add new structured_annotation property to retrieve a version annotation as a dict
- **Cleansing**: Detect uncleansed assets in unpublished bucket (for use before publication)

### Refactor

- **VersionAnnotation**: move VersionAnnotation and associated bits into Document model subclass

## v42.0.0 (2025-10-24)

### BREAKING CHANGE

- Merge check methods in the `Document` class now live in the new `MergeManager` class.

### Feat

- **Document**: add new method to check a document can be merged into a given target
- **Document**: merge source checks now ensure a document is safe to delete
- **Document**: merge source checks now ensure a document has never been published
- **Document**: add new methods to check if a document is safe to use as merge source

### Fix

- **Document**: merge source checks now check the source is not a specific version
- **Document**: merge target checks now check the target is not a specific version
- **Document**: merge target checks now make sure you're not merging a document with itself
- **deps**: update dependency certifi to >=2025.10.5,<2025.11.0
- **deps**: update dependency boto3 to v1.40.36
- **deps**: update dependency lxml to v6.0.2
- **deps**: update dependency boto3 to v1.40.34

### Refactor

- **MergeManager**: move existing merge integrity checks to new MergeManager class

## v41.1.3 (2025-09-10)

### Feat

- **Search**: adds neutral_citation and consignment_number as search options

## v41.1.2 (2025-09-10)

### Fix

- **has_unique_content_hash**: fix return signature for unique document xquery

## v41.1.1 (2025-09-10)

### Fix

- **has_unique_content_hash**: correctly exclude document versions from checking for duplicate hashes

## v41.1.0 (2025-09-09)

### Feat

- **Document**: first_published_datetime now interprets sentinel values

### Fix

- **DocumentFactory**: document factories now correctly set a default first published datetime
- **deps**: update dependency boto3 to v1.40.25
- **deps**: update dependency boto3 to v1.40.22
- **deps**: update dependency ds-caselaw-utils to v2.7.1
- **deps**: update dependency ds-caselaw-utils to v2.7.0
- **deps**: update dependency boto3 to v1.40.20
- **deps**: update dependency boto3 to v1.40.17
- **deps**: update dependency typing-extensions to v4.15.0
- **deps**: update dependency boto3 to v1.40.16
- **deps**: update dependency lxml to v6.0.1
- **deps**: update dependency boto3 to v1.40.13

## v40.0.0 (2025-08-20)

## v41.0.0 (2025-09-02)

- Added `api_client.has_unique_content_hash`
- Added `Document.has_unique_content_hash`
- Extended `Document`'s `attributes_to_validate` to consider `has_unique_content_hash`
- **Reparse/Enrichment**: Don't reparse/enrich documents that have external data

## v40.0.0 (2025-08-20)

### Feat

- **DocumentBody**: update category to match the first category without a parent
- **DocumentBody**: add a categories function that returns all categories and related subcategories for a document

### BREAKING CHANGE

- `SearchResult` will no longer return `""` when a Neutral Citation Number is missing. Instead, it will return `None`.
- Minimum Python version has changed from 3.10 to 3.12

### Feat

- **Document**: add new has_ever_been_published property
- **Document**: documents can now retrieve and will set first_published_datetime
- **Client**: add methods for getting/setting datetime properties in MarkLogic
- **SearchResult**: neutral_citation of a search result is now derived from structured identifiers
- change minimum Python version from 3.10 to 3.12

## v39.2.1 (2025-08-14)

- **Enrichment**: When publishing, don't fail if the document is unenrichable

## v39.2.0 (2025-08-13)

### Changed

- **Eval**: Set configurable timeouts when evaling against MarkLogic: default 3.05s (connect) and 10s (read)
- Updated `ds-caselaw-utils` to `v2.5.0` to support more historic tribunal court definitions

## v39.1.1 (2025-08-07)

- **Github Actions**: Migrate from CodeClimate to Codecov

## v39.1.0 (2025-07-28)

### Fix

- Fixed `document.force_reparse` for parser failures, specifically when we do not know whether it should be a press summary or judgment

## v39.0.0 (2025-07-16)

### BREAKING CHANGE

- IdentifiersCollection.validate_uuids_match_keys() now returns SuccessFailureMessageTuple instead of None

### Feat

- **IdentifiersCollection**: add method to return all possible new identifier types for collection
- **IdentifiersCollection**: add validation for only one non-deprecated identifier of type
- **IdentifiersCollection**: validating UUID integrity now returns success/failure and message rather than exception
- **Document**: break identifier validation into own method
- **Identifier**: deprecated identifiers score 0 during ranking

### Fix

- **deps**: update dependency certifi to v2025.7.14
- **deps**: update dependency boto3 to v1.39.4
- **deps**: update dependency certifi to >=2025.7.9,<2025.8.0
- **Document**: don't add spurious akn: namespaces to live xml

### Refactor

- **IdentifiersCollection**: refactor getting all identifiers by schema so it's clearer
- **IdentifiersCollection**: break up validation functions to improve readability
- **IdentifiersCollection**: refactor how we run collection-level validations to support message bubbling

## v38.0.0 (2025-07-07)

### BREAKING CHANGE

- `identifiers.Identifiers` is now `identifiers.collection.IdentifierCollection`
- `Identifiers.validate()` is now `Identifiers.validate_uuids_match_keys()`
- `IdentifierSchema.validate_identifier` has been renamed `IdentifierSchema.validate_identifier_value`

### Feat

- **identifiers**: canonical list of supported identifiers now lives in identifiers.collection
- **Document**: saving identifiers now correctly raises exception when validation fails
- move to using structured objects to represent validation failures rather than exceptions
- **Identifiers**: validating identifiers now performs a full check of all individual identifiers
- **Identifier**: add ability to validate that an identifier is acceptable for a given document class
- **IdentifierSchema**: rename validate_identifier to validate_identifier_value
- **Identifier**: add ability to validate that identifiers are globally unique
- **IdentifierSchema**: add new allow_editing flag to identifier schemas
- **Document**: expose xml with dynamic FRBR uris from document properties using XLST

### Fix

- **deps**: update dependency boto3 to v1.38.42
- **deps**: update boto packages to v1.38.39
- **deps**: update dependency boto3 to v1.38.37
- **deps**: update dependency certifi to >=2025.6.15,<2025.7.0
- **deps**: update dependency boto3 to v1.38.36
- **deps**: update dependency boto3 to v1.38.33
- **deps**: update dependency requests to v2.32.4 [security]
- **deps**: update dependency ds-caselaw-utils to v2.4.7
- **deps**: update dependency boto3 to v1.38.31
- **deps**: update dependency boto3 to v1.38.28
- **deps**: update dependency typing-extensions to v4.14.0

### Refactor

- **Identifiers**: rename Identifiers to IdentifierCollection and move to submodule
- refine how identifiers validity checks are performed

## v37.4.0 (2025-06-04)

### Feat

- **Identifier**: add the ability to store and retrieve if an identifier is deprecated

### Fix

- **deps**: update dependency boto3 to v1.38.27
- **deps**: update dependency mypy-boto3-s3 to v1.38.26
- **deps**: update dependency boto3 to v1.38.24

## v37.3.1 (2025-05-28)

### Fix

- **extract_version**: update version decoding regex so it accepts new-style URIs
- **deps**: update dependency boto3 to v1.38.22

### Refactor

- remove unused namespace declarations from codebase
- **Document**: improve type hints for versions_as_documents

## v37.3.0 (2025-05-22)

### Feat

- Add `only_with_html_representation` field to `SearchParameters` dataclass

## v37.2.0 (2025-05-20)

### Feat

- **SearchResultFactory**: search result factory now includes identifier map

### Fix

- **deps**: update dependency boto3 to v1.38.17
- **deps**: update dependency sqids to v0.5.2
- **deps**: update dependency ds-caselaw-utils to v2.4.6

## v37.1.0 (2025-05-15)

### Feat

- **MarklogicApiClient**: add new method for getting list of documents missing a FCLID
- Remove warning about `verify unpublished judgments` being called.

### Fix

- **deps**: update dependency ds-caselaw-utils to v2.4.5
- **deps**: update dependency boto3 to v1.38.14
- **deps**: update dependency ds-caselaw-utils to v2.4.4

### Refactor

- break FCLID minting into its own function at document level

## v37.0.2 (2025-05-13)

### Fix

- **SearchResultFactory**: fix type mismatch in factory default

## v37.0.1 (2025-05-13)

### Fix

- **SearchResultFactory**: improve fidelity to actual MarkLogic response
- **deps**: update dependency boto3 to v1.38.12
- **deps**: update dependency boto3 to v1.38.9
- **deps**: update dependency charset-normalizer to v3.4.2
- **deps**: update dependency boto3 to v1.38.7

## v37.0.0 (2025-05-02)

### BREAKING CHANGE

- content_as_html renamed to content_html to fix assets not rendering
  - signature changed, now takes full prefix to folder containing assets
  - location of assets now mandatory

## v36.0.2 (2025-05-01)

### Fix

- [FCL-841] Resolve NCN pattern matching for EWCOP T3

## v36.0.1 (2025-04-30)

### Feat

- **SearchResultFactory**: now closer matches a real `SearchResult` so it's more useful downstream

## v36.0.0 (2025-04-28)

### BREAKING CHANGE

- An identifier's document_published is natively boolean from MarkLogic, treat it as such
- `NeutralCitationNumber`s must now be valid in all conditions, including under test.

### Feat

- **NeutralCitationNumber**: validating an NCN now checks it can be converted to a URL
- **Identifiers**: run identifier validation methods on init

### Fix

- **deps**: update dependency certifi to >=2025.4.26,<2025.5.0
- **deps**: update dependency boto3 to v1.38.2
- **deps**: update dependency boto3 to v1.37.38
- **deps**: update dependency ds-caselaw-utils to v2.4.3
- **deps**: update dependency ds-caselaw-utils to v2.4.2
- **deps**: update dependency ds-caselaw-utils to v2.4.1
- **deps**: update dependency boto3 to v1.37.35

## v35.1.1 (2025-04-17)

### Fix

- Reinstate PRIVATE_ASSET_BUCKET_REGION environment variable to fix NoRegionError

## v35.1.0 (2025-04-16)

### Feat

- **identifiers**: swap priorities of FCLID and PressSummaryRelatedNCNIdentifier

### Fix

- **deps**: update dependency boto3 to v1.37.34
- **deps**: update dependency lxml to v5.3.2
- **deps**: update dependency boto3 to v1.37.31
- **deps**: update dependency typing-extensions to v4.13.2

## v35.0.0 (2025-04-03)

- Remove explicit environment variables to configure AWS; rely on magic ones

## v34.1.2 (2025-03-26)

- Allow AWS client to be initalised without an AccessKey.

## v34.1.1 (2025-03-13)

## Fix

- Allow XML documents to be read as Documents even if they don't have a collection

## v34.1.0 (2025-03-13)

### Feat

- Add new `ParserLog` document class to handle proper storage of error logs

### Fix

- **deps**: update dependency boto3 to v1.37.10
- **deps**: update dependency boto3 to v1.37.8

## v34.0.2 (2025-03-07)

## Fix

- Search results should return their own identifiers, not the first search result's

## v34.0.1 (2025-03-04)

## Fix

- get_document_type_class was not working with actual documents

## v34.0.0 (2025-03-05)

### BREAKING CHANGE

- Python versions below 3.10 are no longer supported.
- insert_document_xml() now requires a Document type class be provided

### Feat

- **FCL-735**: inserting a new document requires an explicit document type collection
- `SearchResults` now includes an `identifiers` property

### Fix

- **deps**: update dependency boto3 to v1.37.3

## v33.0.0 (2025-02-19)

### Breaking Changes

- Stop validating xml against schema when attempting to update a locked judgment

## v32.0.0 (2025-02-19)

### Breaking Changes

- Removed unneded `can_enrich` method from API
- Stop validating xml against schema before attempting to trigger enrichment

### Changes

- Add logging for enrich method for debugging

## v31.2.0 (2025-02-12)

### Feat

- **Identifier**: update the types of outputs from value and slug

### Fix

- **deps**: update dependency lxml to v5.3.1

## v31.1.0 (2025-02-10)

### Feat

- **types**: MarkLogicDocumentURIString now validates and can be converted back to a DocumentURIString

### Fix

- **deps**: update boto packages to v1.36.15
- **IdentifierResolution**: fix incorrect types in resolving an identifier

## v31.0.1 (2025-02-06)

### Fix

- **html transform**: If query contains space, don't delete the highlighted space
- **deps**: update dependency pytz to v2025
- **deps**: update dependency boto3 to v1.36.12

## v31.0.0 (2025-02-03)

### Breaking Change

- refactor(Document): remove deprecated content_as_html and number_of_mentions methods

### Feat

- FCL 582 Get related documents (e.g. Press Summary for Judgment)

### Fix

- Relax has_content to not require valid akomaNtoso
- fix(DocumentFactory): make default body XML representative of a real document

## v30.0.0 (2025-01-31)

### Feat

- **identifiers**: Support identifier resolution from value and namespace
- ⚠️ **refactor**: Move DocumentURIString and InvalidDocumentURIException to .types
- ⚠️ **html transform**: Document.body.content_as_html can be None if there is no real content

## v29.2.0 (2025-01-27)

### Feat

- **NeutralCitationMixin**: NCNs are no longer considered obligatory

### Fix

- **s3**: When publishing, only copy files in folder, not all folders that share a prefix
- **deps**: update dependency boto3 to v1.36.6
- **deps**: update boto packages to v1.36.3

## v29.1.1 (2025-01-20)

### Fix

- **deps**: update dependency boto3 to v1.36.1
- **deps**: update dependency django-environ to ^0.12.0
- **deps**: update dependency boto3 to v1.35.98
- **deps**: update dependency boto3 to v1.35.96
- **deps**: update boto packages to v1.35.93
- **deps**: update dependency boto3 to v1.35.93

## v29.1.0 (2025-01-08)

### Feat

- **FCL-568**: add new class for Press Summary identifiers

### Fix

- **deps**: update dependency mypy-boto3-s3 to v1.35.92
- **deps**: update dependency boto3 to v1.35.91
- **deps**: update dependency boto3 to v1.35.88
- **deps**: update dependency charset-normalizer to v3.4.1
- **deps**: update dependency boto3 to v1.35.87
- **deps**: update dependency boto3 to v1.35.85

## v29.0.1 (2024-12-20)

### Fix

- **Identifiers**: preferred identifier now correctly handles case where there are none of type
- **Identifiers**: fix case where unpacking unknown identifier type would raise an exception
- **deps**: update dependency mypy-boto3-s3 to v1.35.81
- **deps**: update dependency boto3 to v1.35.82

## v29.0.0 (2024-12-18)

### BREAKING CHANGE

- Methods which were previously guaranteed to return a Neutral Citation may now return `None`.

### Feat

- **FCL-533**: getting scored or preferred identifiers can now be done by type
- **FCL-533**: modify human identifier to rely on identifiers framework
- **FCL-533**: add scoring to Identifiers

### Fix

- **IdentifierSchema**: use hasattr instead of getattr with a default when testing required attributes

## v28.2.0 (2024-12-17)

### Feat

- **FCL-532**: assign FCLIDs on document publication
- **FCL-532**: add ability to retrieve identifiers by type
- **FCL-499**: add new FCLID identifier class
- **FCL-499**: add method to get next sequence number from MarkLogic

### Fix

- **deps**: update dependency certifi to >=2024.12.14,<2024.13.0
- **deps**: update dependency boto3 to v1.35.80

## v28.1.0 (2024-12-12)

### Feat

- **FCL-309**: identifier UUIDs are now prefixed with 'id-'
- **FCL-309**: identifiers can compile URL slugs
- **FCL-309**: identifiers can now be saved to and retrieved from MarkLogic
- **FCL-309**: add functionality for packing and unpacking XML representations of identifiers
- **FCL-309**: add stub for defining identifier schemas, and a Neutral Citation schema
- **FCL-309**: add ability to add, delete and update identifiers

### Fix

- **deps**: update boto packages to v1.35.69
- **deps**: update dependency ds-caselaw-utils to v2.0.1
- **deps**: update dependency mypy-boto3-sns to v1.35.68
- **deps**: update boto packages to v1.35.67
- **deps**: update dependency boto3 to v1.35.64
- **deps**: update boto packages to v1.35.61
- **deps**: update dependency boto3 to v1.35.77
- **deps**: update dependency mypy-boto3-s3 to v1.35.76
- **deps**: update dependency boto3 to v1.35.75
- **deps**: update boto packages to v1.35.72

## v28.0.0 (2024-11-14)

### BREAKING CHANGE

- Code which provided unsanitised URIs when initialising `DocumentURIStrings` will now cause `InvalidDocumentURIException`s to be raised.
- Document can now no longer be initialised with a string as the `uri`, it must be a `DocumentURIString`.

### Feat

- Validate strings when creating a new DocumentURIString

### Fix

- **deps**: update dependency boto3 to v1.35.58
- **deps**: update dependency boto3 to v1.35.56

### Refactor

- **Document**: initialising a Document now requires a DocumentURIString, not a str
- **tests**: simpler test changes to pass type checking

## v27.4.0 (2024-11-07)

### Change of behaviour

- Require documents to be published before bulk enrichment will enrich them

### Feature

- Add logging of xquery commands and values passed to them if DEBUG environment set

## v27.3.0 (2024-10-30)

### Feat

- **FCL-386**: search query can now be passed to get_document_by_uri

## v27.2.0 (2024-10-28)

## Feat

- **FCL-396**: query highlighting is now done as a function of requesting the Document

### Fix

- **deps**: update dependency boto3 to v1.35.48
- **deps**: update dependency mypy-boto3-s3 to v1.35.45
- **deps**: update dependency boto3 to v1.35.45

### Refactor

- **FCL-396**: tidy up API implementation for search query highlighting change

## v27.1.0 (2024-10-23)

- Feature: Add native XSLT transformations to the API
- Allow things on doc.body to be called from doc with a warning
- client.checkout_judgment now accepts a `timeout_seconds` parameter
- Allow test failures for Python 3.13/3.14
- Ensure Judgment- and PressSummaryFactory have working NCNs

## v27.0.1 (2024-10-17)

- Fix `.content_as_html` on Document Factory

## v27.0.0 (2024-10-08)

### BREAKING CHANGE

- Remove `Document.overwrite` and `MarkLogicApiClient.overwrite`
- The `models.documents.body.CourtIdentifierString` type has been replaced with the more specific `courts.CourtCode` type from ds-caselaw-utils.

### Feat

- **NeutralCitationMixin**: use ABC to flag abstract methods properly

### Fix

- **deps**: update dependency boto3 to v1.35.33
- **deps**: update dependency mypy-boto3-s3 to v1.35.32
- **deps**: update dependency boto3 to v1.35.30
- **SearchResponse**: total now returns an int, not a str
- **SearchResult**: update behaviour to meet type checking
- **deps**: update dependency ds-caselaw-utils to v1.7.0
- **deps**: update dependency boto3 to v1.35.28
- **deps**: update dependency ds-caselaw-utils to v1.5.7

### Refactor

- **FCL-331**: move api_client, xml and html params to build method signature instead of kwargs
- **types**: typing improvements around NeutralCitationString
- **Document**: remove unused overwrite method
- **DocumentBody**: replace CourtIdentifierString with utils.courts.CourtCode

## v26.0.0 (2024-09-25)

### BREAKING CHANGE

- Multiple methods which used to be within `Document` are now in `Document.body`

### Feat

- **FCL-268**: break functions which rely on the document body into their own subclass

### Fix

- **FCL-268**: update factory behaviour to match new document body model
- **FCL-268**: use real date when testing if document date should be sent in reparse payload
- **deps**: update dependency boto3 to v1.35.23

### Refactor

- **FCL-268**: move document statuses to their own submodule
- **FCL-268**: move document exceptions into their own submodule
- **FCL-268**: move XML manipulation into its own file
- **FCL-268**: move the documents module in readiness for better code separation

## [Release 25.0.0]

- **Breaking:** Remove xml_tools
- Multiple stylistic improvements, and enabling ruff to allow us to keep standards up in future

## [Release 24.0.1]

- Truncate reparse references to avoid overlong step function names in TRE

## [Release 24.0.0]

- Always set last sent date to parser, even on failed parses
- [FCL-176] Tooling configuration audit
- [FCL-195] Skip pre-commit branch check in CI
- Make enrichment date maths not care about timezones

## [Release 23.0.2]

- Remove explicit urllib3 v1 dependency, rely on implicit dependency only

## [Release 23.0.1]

- Remove fcl*ex_id* prefix from UUID of reparse execution ID
- Implement handling of facets received from MarkLogic search results

## [Release 22.1.0]

- Add an `enriched_recently` property
- Add a `validates_against_schema` property
- Add a `can_enrich` property
- Only enrich if not recently enriched and valid against current schema
- Allow fetching linked documents for `Judgement`s and `PressSummary`s
- Add function to check if the docx exists for a judgment

## [Release 22.0.2]

- Add a method to allow fetching press summaries for a given document

## [Release 22.0.1]

- Ensure that we log a warning and do not error when a judgment has an unrecognised jurisdiction

## [Release 22.0.0]

- Expose court jurisdictions in search results

## [Release 21.0.0]

- **Breaking:** `Client.get_pending_enrichment_for_version` now requires both a target enrichment version and a target parser version, and will not include documents which have not been parsed with the target version.
- **Feature:** Add accessors for judgment jurisdiction

## [Release 20.0.0]

- **Feature:** New `Client.get_pending_parse_for_version` and `Client.get_highest_parser_version` methods to help find documents in need of re-parsing.
- **Breaking:** `Client.get_pending_enrichment_for_version` now accepts a tuple of `(major_version, minor_version)` rather than a single major version.

## [Release 19.1.0]

- Add support for quoted phrase prioritisation in result snippets

## [Release 19.0.0]

- **Breaking**: `Client.set_published` no longer has a default argument; you must always be explicit.
- **Feature:** New `Client.get_pending_enrichment_for_version` method finds documents which are not yet enriched with a given version, and which haven't recently been sent for enrichment.

## [Release 18.0.0]

- **Breaking:** Fully remove the deprecated `caselawclient.api_client` instance.
- **Breaking:** Remove top-level methods for interacting with a document's XML representation. These are now all encapsulated in `document.xml`, which is an instance of `Document.XML`.
- **Feature:** New `Document.xml_root_element` function to replace `get_judgment_root`
- **Feature:** Documents which are not valid XML are now identified by the raising of a new `Document.NonXMLDocumentError` exception
- **Feature:** Add method to return document's lock status and message.

## [Release 17.3.0]

- **Feature:** `Document.enrich()` method will send a message to the announce SNS, requesting that a document be enriched.

## [Release 17.2.0]

- `document.content_as_html` now takes an optional `query=` string parameter, which, when supplied, highlights instances of the query within the document with `<mark>` tags, each of which has a numbered id indicating its sequence in the document.
- `document.number_of_mentions` method which takes a `query=` string parameter, and returns the number of highlighted mentions in the html.

## [Release 17.1.0]

- New `Client.get_combined_stats_table` method to run a combined statistics query against MarkLogic.

## [Release 17.0.0]

- BREAKING: `VersionAnnotation` now requires a statement of if the action is automated or not
- `VersionAnnotation` can now accept an optional dict of structured `payload` data
- `VersionAnnotation` can now record a user agent string

## [Release 16.0.0]

- New versions of a document created with `insert_document_xml` can now be annotated
- BREAKING: Renamed `save_judgment_xml` to `update_document_xml`
- BREAKING: All annotations for versions are now mandatory instances of the new `VersionAnnotation` class

## [Release 15.1.2]

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

- Refactored `Document` class' `name`, `court`, `document_date_as_string` and `document_date_as_date` (previously judgment*date*...) on Document class and neutral_citation on Judgment class making use of the new cached `content_as_xml_tree` property.
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
  This is potentially a _breaking change_ if implementations have been relying on duck typing.
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

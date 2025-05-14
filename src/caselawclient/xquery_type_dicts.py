# This file is built automatically with script/build_xquery_type_dicts.
# DO NOT CHANGE IT MANUALLY!

"""
These classes are automatically generated using the `script/build_xquery_type_dicts` script, as part of pre-commit
checks. They are used to enforce appropriately typed variables being passed in to MarkLogic XQuery functions.
"""

from typing import Any, NewType, Optional, TypedDict
from caselawclient.types import DocumentURIString, DocumentIdentifierSlug, DocumentIdentifierValue
from caselawclient.types import MarkLogicDocumentURIString as MarkLogicDocumentURIString

MarkLogicDocumentVersionURIString = NewType("MarkLogicDocumentVersionURIString", MarkLogicDocumentURIString)

MarkLogicPrivilegeURIString = NewType("MarkLogicPrivilegeURIString", str)

class MarkLogicAPIDict(TypedDict):
    pass


# break_judgment_checkout.xqy
class BreakJudgmentCheckoutDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# checkin_judgment.xqy
class CheckinJudgmentDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# checkout_judgment.xqy
class CheckoutJudgmentDict(MarkLogicAPIDict):
    annotation: str
    timeout: int
    uri: MarkLogicDocumentURIString


# copy_document.xqy
class CopyDocumentDict(MarkLogicAPIDict):
    new_uri: MarkLogicDocumentURIString
    old_uri: MarkLogicDocumentURIString


# delete_judgment.xqy
class DeleteJudgmentDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# document_collections.xqy
class DocumentCollectionsDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# document_exists.xqy
class DocumentExistsDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# get_components_for_document.xqy
class GetComponentsForDocumentDict(MarkLogicAPIDict):
    component: str
    parent_uri: DocumentURIString


# get_judgment.xqy
class GetJudgmentDict(MarkLogicAPIDict):
    search_query: Optional[str]
    show_unpublished: Optional[bool]
    uri: MarkLogicDocumentURIString
    version_uri: Optional[MarkLogicDocumentVersionURIString]


# get_judgment_checkout_status.xqy
class GetJudgmentCheckoutStatusDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# get_judgment_version.xqy
class GetJudgmentVersionDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString
    version: str


# get_last_modified.xqy
class GetLastModifiedDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# get_missing_fclid.xqy
class GetMissingFclidDict(MarkLogicAPIDict):
    maximum_records: Optional[int]


# get_pending_enrichment_for_version.xqy
class GetPendingEnrichmentForVersionDict(MarkLogicAPIDict):
    maximum_records: Optional[int]
    target_enrichment_major_version: int
    target_enrichment_minor_version: int
    target_parser_major_version: int
    target_parser_minor_version: int


# get_pending_parse_for_version.xqy
class GetPendingParseForVersionDict(MarkLogicAPIDict):
    maximum_records: Optional[int]
    target_major_version: int
    target_minor_version: int


# get_properties_for_search_results.xqy
class GetPropertiesForSearchResultsDict(MarkLogicAPIDict):
    uris: list[Any]


# get_property.xqy
class GetPropertyDict(MarkLogicAPIDict):
    name: str
    uri: MarkLogicDocumentURIString


# get_property_as_node.xqy
class GetPropertyAsNodeDict(MarkLogicAPIDict):
    name: str
    uri: MarkLogicDocumentURIString


# get_version_annotation.xqy
class GetVersionAnnotationDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# get_version_created.xqy
class GetVersionCreatedDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# insert_document.xqy
class InsertDocumentDict(MarkLogicAPIDict):
    annotation: str
    document: str
    type_collection: str
    uri: MarkLogicDocumentURIString


# list_judgment_versions.xqy
class ListJudgmentVersionsDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# resolve_from_identifier_slug.xqy
class ResolveFromIdentifierSlugDict(MarkLogicAPIDict):
    identifier_slug: DocumentIdentifierSlug
    published_only: Optional[int]


# resolve_from_identifier_value.xqy
class ResolveFromIdentifierValueDict(MarkLogicAPIDict):
    identifier_value: DocumentIdentifierValue
    published_only: Optional[int]


# set_boolean_property.xqy
class SetBooleanPropertyDict(MarkLogicAPIDict):
    name: str
    uri: MarkLogicDocumentURIString
    value: str


# set_metadata_citation.xqy
class SetMetadataCitationDict(MarkLogicAPIDict):
    content: str
    uri: MarkLogicDocumentURIString


# set_metadata_court.xqy
class SetMetadataCourtDict(MarkLogicAPIDict):
    content: str
    uri: MarkLogicDocumentURIString


# set_metadata_jurisdiction.xqy
class SetMetadataJurisdictionDict(MarkLogicAPIDict):
    content: str
    uri: MarkLogicDocumentURIString


# set_metadata_name.xqy
class SetMetadataNameDict(MarkLogicAPIDict):
    content: str
    uri: MarkLogicDocumentURIString


# set_metadata_this_uri.xqy
class SetMetadataThisUriDict(MarkLogicAPIDict):
    content_with_id: str
    content_with_xml: str
    content_without_id: str
    uri: MarkLogicDocumentURIString


# set_metadata_work_expression_date.xqy
class SetMetadataWorkExpressionDateDict(MarkLogicAPIDict):
    content: str
    uri: MarkLogicDocumentURIString


# set_property.xqy
class SetPropertyDict(MarkLogicAPIDict):
    name: str
    uri: MarkLogicDocumentURIString
    value: str


# set_property_as_node.xqy
class SetPropertyAsNodeDict(MarkLogicAPIDict):
    name: str
    uri: MarkLogicDocumentURIString
    value: str


# update_document.xqy
class UpdateDocumentDict(MarkLogicAPIDict):
    annotation: str
    judgment: str
    uri: MarkLogicDocumentURIString


# update_locked_judgment.xqy
class UpdateLockedJudgmentDict(MarkLogicAPIDict):
    annotation: str
    judgment: str
    uri: MarkLogicDocumentURIString


# user_has_privilege.xqy
class UserHasPrivilegeDict(MarkLogicAPIDict):
    privilege_action: str
    privilege_uri: MarkLogicPrivilegeURIString
    user: str


# user_has_role.xqy
class UserHasRoleDict(MarkLogicAPIDict):
    role: str
    user: str


# validate_document.xqy
class ValidateDocumentDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# xslt.xqy
class XsltDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# xslt_transform.xqy
class XsltTransformDict(MarkLogicAPIDict):
    img_location: Optional[str]
    query: Optional[str]
    show_unpublished: Optional[bool]
    uri: MarkLogicDocumentURIString
    version_uri: Optional[MarkLogicDocumentVersionURIString]
    xsl_filename: Optional[str]

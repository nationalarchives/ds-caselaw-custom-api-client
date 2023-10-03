# This file is built automatically with script/build_xquery_type_dicts.
# DO NOT CHANGE IT MANUALLY!

"""
These classes are automatically generated using the `script/build_xquery_type_dicts` script, as part of pre-commit
checks. They are used to enforce appropriately typed variables being passed in to MarkLogic XQuery functions.
"""

from typing import Any, NewType, Optional, TypedDict

MarkLogicDocumentURIString = NewType("MarkLogicDocumentURIString", str)
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


# get_judgment.xqy
class GetJudgmentDict(MarkLogicAPIDict):
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


# get_properties_for_search_results.xqy
class GetPropertiesForSearchResultsDict(MarkLogicAPIDict):
    uris: list[Any]


# get_property.xqy
class GetPropertyDict(MarkLogicAPIDict):
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
    uri: MarkLogicDocumentURIString


# list_judgment_versions.xqy
class ListJudgmentVersionsDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


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


# xslt.xqy
class XsltDict(MarkLogicAPIDict):
    uri: MarkLogicDocumentURIString


# xslt_transform.xqy
class XsltTransformDict(MarkLogicAPIDict):
    img_location: Optional[str]
    show_unpublished: Optional[bool]
    uri: MarkLogicDocumentURIString
    version_uri: Optional[MarkLogicDocumentVersionURIString]
    xsl_filename: Optional[str]

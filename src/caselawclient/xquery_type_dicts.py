# This file is built automatically with script/build_xquery_type_dicts.
# DO NOT CHANGE IT MANUALLY!

from typing import Any, Optional, TypedDict


class MarkLogicAPIDict(TypedDict):
    pass


# break_judgment_checkout.xqy
class BreakJudgmentCheckoutDict(MarkLogicAPIDict):
    uri: str


# checkin_judgment.xqy
class CheckinJudgmentDict(MarkLogicAPIDict):
    uri: str


# checkout_judgment.xqy
class CheckoutJudgmentDict(MarkLogicAPIDict):
    annotation: str
    timeout: int
    uri: str


# copy_judgment.xqy
class CopyJudgmentDict(MarkLogicAPIDict):
    new_uri: str
    old_uri: str


# delete_judgment.xqy
class DeleteJudgmentDict(MarkLogicAPIDict):
    uri: str


# get_judgment.xqy
class GetJudgmentDict(MarkLogicAPIDict):
    show_unpublished: Optional[bool]
    uri: str
    version_uri: Optional[str]


# get_judgment_checkout_status.xqy
class GetJudgmentCheckoutStatusDict(MarkLogicAPIDict):
    uri: str


# get_judgment_version.xqy
class GetJudgmentVersionDict(MarkLogicAPIDict):
    uri: str
    version: str


# get_last_modified.xqy
class GetLastModifiedDict(MarkLogicAPIDict):
    uri: str


# get_metadata_citation.xqy
class GetMetadataCitationDict(MarkLogicAPIDict):
    uri: str


# get_metadata_court.xqy
class GetMetadataCourtDict(MarkLogicAPIDict):
    uri: str


# get_metadata_name.xqy
class GetMetadataNameDict(MarkLogicAPIDict):
    uri: str


# get_metadata_work_date.xqy
class GetMetadataWorkDateDict(MarkLogicAPIDict):
    uri: str


# get_properties_for_search_results.xqy
class GetPropertiesForSearchResultsDict(MarkLogicAPIDict):
    uris: list[Any]


# get_property.xqy
class GetPropertyDict(MarkLogicAPIDict):
    name: str
    uri: str


# insert_judgment.xqy
class InsertJudgmentDict(MarkLogicAPIDict):
    judgment: str
    uri: str


# judgment_exists.xqy
class JudgmentExistsDict(MarkLogicAPIDict):
    uri: str


# list_judgment_versions.xqy
class ListJudgmentVersionsDict(MarkLogicAPIDict):
    uri: str


# set_boolean_property.xqy
class SetBooleanPropertyDict(MarkLogicAPIDict):
    name: str
    uri: str
    value: str


# set_metadata_citation.xqy
class SetMetadataCitationDict(MarkLogicAPIDict):
    content: str
    uri: str


# set_metadata_court.xqy
class SetMetadataCourtDict(MarkLogicAPIDict):
    content: str
    uri: str


# set_metadata_name.xqy
class SetMetadataNameDict(MarkLogicAPIDict):
    content: str
    uri: str


# set_metadata_this_uri.xqy
class SetMetadataThisUriDict(MarkLogicAPIDict):
    content_with_id: str
    content_with_xml: str
    content_without_id: str
    uri: str


# set_metadata_work_expression_date.xqy
class SetMetadataWorkExpressionDateDict(MarkLogicAPIDict):
    content: str
    uri: str


# set_property.xqy
class SetPropertyDict(MarkLogicAPIDict):
    name: str
    uri: str
    value: str


# update_judgment.xqy
class UpdateJudgmentDict(MarkLogicAPIDict):
    annotation: str
    judgment: str
    uri: str


# update_locked_judgment.xqy
class UpdateLockedJudgmentDict(MarkLogicAPIDict):
    annotation: str
    judgment: str
    uri: str


# user_has_privilege.xqy
class UserHasPrivilegeDict(MarkLogicAPIDict):
    privilege_action: str
    privilege_uri: str
    user: str


# user_has_role.xqy
class UserHasRoleDict(MarkLogicAPIDict):
    role: str
    user: str


# xslt.xqy
class XsltDict(MarkLogicAPIDict):
    uri: str


# xslt_transform.xqy
class XsltTransformDict(MarkLogicAPIDict):
    img_location: Optional[str]
    show_unpublished: Optional[bool]
    uri: str
    version_uri: Optional[str]
    xsl_filename: Optional[str]

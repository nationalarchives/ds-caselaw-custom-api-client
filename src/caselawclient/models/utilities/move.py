import xml.etree.ElementTree as ET
from typing import Any, Optional

import ds_caselaw_utils as caselawutils

from caselawclient.errors import MarklogicAPIError
from caselawclient.models.judgments import Judgment
from caselawclient.models.utilities.aws import copy_assets


class NeutralCitationToUriError(Exception):
    pass


class OverwriteJudgmentError(Exception):
    pass


class MoveJudgmentError(Exception):
    pass


def overwrite_document(
    source_uri: str,
    target_citation: str,
    api_client: Any,
) -> str:
    """Move the document at source_uri on top of the new citation, which must already exist
    Compare to update_document_uri

    :param source_uri: The URI with the contents of the document to be written. (possibly a failure url)
    :param target_citation: The NCN (implying a URL) whose contents will be overwritten
    :param api_client: An instance of MarklogicApiClient used to make the search request
    :return: The URL associated with the `target_citation`
    """

    new_uri: Optional[str] = caselawutils.neutral_url(target_citation.strip())

    if new_uri == source_uri:
        raise RuntimeError(
            f"Attempted to overwrite document {source_uri} with itself, which is not permitted."
        )
    if new_uri is None:
        raise NeutralCitationToUriError(
            f"Unable to form new URI for {source_uri} from neutral citation: {target_citation}"
        )
    if not api_client.document_exists(new_uri):
        raise OverwriteJudgmentError(
            f"The URI {new_uri} generated from {target_citation} does not already exist, so cannot be overwritten"
        )
    old_judgment = Judgment(source_uri, api_client)
    try:
        old_judgment_bytes = old_judgment.content_as_xml
        old_judgment_xml = ET.XML(bytes(old_judgment_bytes, encoding="utf-8"))
        api_client.save_judgment_xml(
            new_uri,
            old_judgment_xml,
            annotation=f"overwritten from {source_uri}",
        )
        set_metadata(source_uri, new_uri, api_client)
        # TODO: consider deleting existing public assets at that location
        copy_assets(source_uri, new_uri)
        api_client.set_judgment_this_uri(new_uri)
    except MarklogicAPIError as e:
        raise OverwriteJudgmentError(
            f"Failure when attempting to copy judgment from {source_uri} to {new_uri}: {e}"
        )

    try:
        api_client.delete_judgment(source_uri)
    except MarklogicAPIError as e:
        raise OverwriteJudgmentError(
            f"Failure when attempting to delete judgment from {source_uri}: {e}"
        )

    return new_uri


def update_document_uri(source_uri: str, target_citation: str, api_client: Any) -> str:
    """
    Move the document at source_uri to the correct location based on the neutral citation
    The new neutral citation *must* not already exist (that is handled elsewhere)

    :param source_uri: The URI with the contents of the document to be written. (possibly a failure url)
    :param target_citation: The NCN (implying an unused URL) where the document will be written to
    :param api_client: An instance of MarklogicApiClient used to make the search request
    :return: The URL associated with the `target_citation`
    """
    new_uri: Optional[str] = caselawutils.neutral_url(target_citation.strip())
    if new_uri is None:
        raise NeutralCitationToUriError(
            f"Unable to form new URI for {source_uri} from neutral citation: {target_citation}"
        )

    if api_client.document_exists(new_uri):
        raise MoveJudgmentError(
            f"The URI {new_uri} generated from {target_citation} already exists, you cannot move this judgment to a"
            f" pre-existing Neutral Citation Number."
        )

    try:
        api_client.copy_document(source_uri, new_uri)
        set_metadata(source_uri, new_uri, api_client)
        copy_assets(source_uri, new_uri)
        api_client.set_judgment_this_uri(new_uri)
    except MarklogicAPIError as e:
        raise MoveJudgmentError(
            f"Failure when attempting to copy judgment from {source_uri} to {new_uri}: {e}"
        )

    try:
        api_client.delete_judgment(source_uri)
    except MarklogicAPIError as e:
        raise MoveJudgmentError(
            f"Failure when attempting to delete judgment from {source_uri}: {e}"
        )

    return new_uri


def set_metadata(old_uri: str, new_uri: str, api_client: Any) -> None:
    source_organisation = api_client.get_property(old_uri, "source-organisation")
    source_name = api_client.get_property(old_uri, "source-name")
    source_email = api_client.get_property(old_uri, "source-email")
    transfer_consignment_reference = api_client.get_property(
        old_uri, "transfer-consignment-reference"
    )
    transfer_received_at = api_client.get_property(old_uri, "transfer-received-at")
    for key, value in [
        ("source-organisation", source_organisation),
        ("source-name", source_name),
        ("source-email", source_email),
        ("transfer-consignment-reference", transfer_consignment_reference),
        ("transfer-received-at", transfer_received_at),
    ]:
        if value is not None:
            api_client.set_property(new_uri, key, value)

    """
    `published` is a boolean property and set differently, technically
    these failures should be unpublished but copy the property just in case.
    """
    published = api_client.get_published(old_uri)
    api_client.set_boolean_property(new_uri, "published", bool(published))

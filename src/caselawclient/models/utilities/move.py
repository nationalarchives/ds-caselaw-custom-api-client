import xml.etree.ElementTree as ET
from typing import Optional

import ds_caselaw_utils as caselawutils

from caselawclient.Client import MarklogicAPIError, api_client  # type:ignore
from caselawclient.models.judgments import Judgment
from caselawclient.models.utilities.aws import copy_assets


class NeutralCitationToUriError(Exception):
    pass


class OverwriteJudgmentError(Exception):
    pass


class MoveJudgmentError(Exception):
    pass


def overwrite_judgment(old_uri: str, new_citation: str) -> str:
    """Move the judgment at old_uri on top of the new citation, which must already exist
    Compare to update_document_uri"""
    new_uri: Optional[str] = caselawutils.neutral_url(new_citation.strip())

    if new_uri == old_uri:
        raise RuntimeError(f"trying to overwrite yourself, {old_uri}")
    if new_uri is None:
        raise NeutralCitationToUriError(
            f"Unable to form new URI for {old_uri} from neutral citation: {new_citation}"
        )
    if not api_client.document_exists(new_uri):
        raise OverwriteJudgmentError(
            f"The URI {new_uri} generated from {new_citation} does not already exist, so cannot be overwritten"
        )
    old_judgment = Judgment(old_uri, api_client)
    try:
        old_judgment_bytes = old_judgment.content_as_xml()
        old_judgment_xml = ET.XML(bytes(old_judgment_bytes, encoding="utf-8"))
        api_client.save_judgment_xml(
            new_uri,
            old_judgment_xml,
            annotation=f"overwritten from {old_uri}",
        )
        set_metadata(old_uri, new_uri)
        # TODO: consider deleting existing public assets at that location
        copy_assets(old_uri, new_uri)
        api_client.set_judgment_this_uri(new_uri)
    except MarklogicAPIError as e:
        raise OverwriteJudgmentError(
            f"Failure when attempting to copy judgment from {old_uri} to {new_uri}: {e}"
        )

    try:
        api_client.delete_judgment(old_uri)
    except MarklogicAPIError as e:
        raise OverwriteJudgmentError(
            f"Failure when attempting to delete judgment from {old_uri}: {e}"
        )

    return new_uri


def update_document_uri(old_uri: str, new_citation: str) -> str:
    """
    Move the document at old_uri to the correct location based on the neutral citation
    The new neutral citation *must* not already exist (that is handled elsewhere)
    """
    new_uri: Optional[str] = caselawutils.neutral_url(new_citation.strip())
    if new_uri is None:
        raise NeutralCitationToUriError(
            f"Unable to form new URI for {old_uri} from neutral citation: {new_citation}"
        )

    if api_client.document_exists(new_uri):
        raise MoveJudgmentError(
            f"The URI {new_uri} generated from {new_citation} already exists, you cannot move this judgment to a"
            f" pre-existing Neutral Citation Number."
        )

    try:
        api_client.copy_document(old_uri, new_uri)
        set_metadata(old_uri, new_uri)
        copy_assets(old_uri, new_uri)
        api_client.set_judgment_this_uri(new_uri)
    except MarklogicAPIError as e:
        raise MoveJudgmentError(
            f"Failure when attempting to copy judgment from {old_uri} to {new_uri}: {e}"
        )

    try:
        api_client.delete_judgment(old_uri)
    except MarklogicAPIError as e:
        raise MoveJudgmentError(
            f"Failure when attempting to delete judgment from {old_uri}: {e}"
        )

    return new_uri


def set_metadata(old_uri: str, new_uri: str) -> None:
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

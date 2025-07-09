from typing import TYPE_CHECKING, Optional, Union

from lxml import etree

from caselawclient.types import SuccessFailureMessageTuple

from . import Identifier, IdentifierSchema
from .fclid import FindCaseLawIdentifier
from .neutral_citation import NeutralCitationNumber
from .press_summary_ncn import PressSummaryRelatedNCNIdentifier

if TYPE_CHECKING:
    from caselawclient.Client import MarklogicApiClient
    from caselawclient.models.documents import Document

SUPPORTED_IDENTIFIER_TYPES: list[type["Identifier"]] = [
    FindCaseLawIdentifier,
    NeutralCitationNumber,
    PressSummaryRelatedNCNIdentifier,
]


class IdentifiersCollection(dict[str, Identifier]):
    def validate_uuids_match_keys(self) -> SuccessFailureMessageTuple:
        for uuid, identifier in self.items():
            if uuid != identifier.uuid:
                return SuccessFailureMessageTuple(
                    False, [f"Key of {identifier} in Identifiers is {uuid} not {identifier.uuid}"]
                )

        return SuccessFailureMessageTuple(True, [])

    def check_only_single_non_deprecated_identifier_where_multiples_not_allowed(self) -> SuccessFailureMessageTuple:
        """Check that only one non-deprecated identifier exists per schema where that schema does not allow multiples."""

        schema_to_identifiers: dict[type[IdentifierSchema], list[Identifier]] = {}

        for identifier in self.values():
            schema = getattr(identifier, "schema", None)
            if schema is not None:
                schema_to_identifiers.setdefault(schema, []).append(identifier)

        for schema, identifiers in schema_to_identifiers.items():
            non_deprecated_identifiers = [i for i in identifiers if not i.deprecated]
            if len(non_deprecated_identifiers) > 1:
                return SuccessFailureMessageTuple(
                    False,
                    [
                        f"Multiple non-deprecated identifiers found for schema '{schema.name}': {', '.join(i.value for i in non_deprecated_identifiers)}"
                    ],
                )

        return SuccessFailureMessageTuple(True, [])

    def perform_all_validations(
        self, document_type: type["Document"], api_client: "MarklogicApiClient"
    ) -> SuccessFailureMessageTuple:
        success = True
        messages: list[str] = []

        # Run collection-level validations
        collection_validations_to_run: list[SuccessFailureMessageTuple] = [
            self.validate_uuids_match_keys(),
            self.check_only_single_non_deprecated_identifier_where_multiples_not_allowed(),
        ]

        for validation in collection_validations_to_run:
            if not validation.success:
                success = False
                messages += validation.messages

        for _, identifier in self.items():
            validations = identifier.perform_all_validations(document_type=document_type, api_client=api_client)
            if validations.success is False:
                success = False

            messages += validations.messages

        return SuccessFailureMessageTuple(success, messages)

    def contains(self, other_identifier: Identifier) -> bool:
        """Does the identifier's value and namespace already exist in this group?"""
        return any(other_identifier.same_as(identifier) for identifier in self.values())

    def add(self, identifier: Identifier) -> None:
        if not self.contains(identifier):
            self[identifier.uuid] = identifier

    def valid_new_identifier_types(self, document_type: type["Document"]) -> list[type[Identifier]]:
        """Return a list of identifier types which can be added to a document of the given type, given identifiers already in this collection."""
        return [
            t
            for t in SUPPORTED_IDENTIFIER_TYPES
            if t.schema.allow_editing
            and (not t.schema.document_types or document_type.__name__ in t.schema.document_types)
        ]

    def __delitem__(self, key: Union[Identifier, str]) -> None:
        if isinstance(key, Identifier):
            super().__delitem__(key.uuid)
        else:
            super().__delitem__(key)

    def of_type(self, identifier_type: type[Identifier]) -> list[Identifier]:
        """Return a list of all identifiers of a given type."""
        uuids = self.keys()
        return [self[uuid] for uuid in list(uuids) if isinstance(self[uuid], identifier_type)]

    def delete_type(self, deleted_identifier_type: type[Identifier]) -> None:
        "For when we want an identifier to be the only valid identifier of that type, delete the others first"
        uuids = self.keys()
        for uuid in list(uuids):
            # we could use compare to .schema instead, which would have diffferent behaviour for subclasses
            if isinstance(self[uuid], deleted_identifier_type):
                del self[uuid]

    @property
    def as_etree(self) -> etree._Element:
        """Return an etree representation of all the Document's identifiers."""
        identifiers_root = etree.Element("identifiers")

        for identifier in self.values():
            identifiers_root.append(identifier.as_xml_tree)

        return identifiers_root

    def by_score(self, type: Optional[type[Identifier]] = None) -> list[Identifier]:
        """
        :param type: Optionally, an identifier type to constrain this list to.

        :return: Return a list of identifiers, sorted by their score in descending order.
        """
        identifiers = self.of_type(type) if type else list(self.values())
        return sorted(identifiers, key=lambda v: v.score, reverse=True)

    def preferred(self, type: Optional[type[Identifier]] = None) -> Optional[Identifier]:
        """
        :param type: Optionally, an identifier type to constrain the results to.

        :return: Return the highest scoring identifier of the given type (or of any type, if none is specified). Returns `None` if no identifier is available.
        """
        if len(self.by_score(type)) == 0:
            return None
        return self.by_score(type)[0]

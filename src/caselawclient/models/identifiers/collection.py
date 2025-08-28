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

    def _list_all_identifiers_by_schema(self) -> dict[type[IdentifierSchema], list[Identifier]]:
        """Get a list of all identifiers, grouped by their schema."""
        identifiers_by_schema: dict[type[IdentifierSchema], list[Identifier]] = {}

        for identifier in self.values():
            identifiers_by_schema.setdefault(identifier.schema, []).append(identifier)

        return identifiers_by_schema

    def check_only_single_non_deprecated_identifier_where_multiples_not_allowed(self) -> SuccessFailureMessageTuple:
        """Check that only one non-deprecated identifier exists per schema where that schema does not allow multiples."""

        for schema, identifiers in self._list_all_identifiers_by_schema().items():
            if schema.allow_multiple:
                continue
            non_deprecated_identifiers = [i for i in identifiers if not i.deprecated]
            if len(non_deprecated_identifiers) > 1:
                return SuccessFailureMessageTuple(
                    False,
                    [
                        f"Multiple non-deprecated identifiers found for schema '{schema.name}': {', '.join(i.value for i in non_deprecated_identifiers)}"
                    ],
                )

        return SuccessFailureMessageTuple(True, [])

    def _perform_collection_level_validations(self) -> SuccessFailureMessageTuple:
        """Perform identifier validations which are only possible at the collection level, such as UUID integrity and identifying exclusivity problems."""

        success = True
        messages: list[str] = []

        collection_validations_to_run: list[SuccessFailureMessageTuple] = [
            self.validate_uuids_match_keys(),
            self.check_only_single_non_deprecated_identifier_where_multiples_not_allowed(),
        ]

        for validation in collection_validations_to_run:
            if not validation.success:
                success = False
                messages += validation.messages

        return SuccessFailureMessageTuple(success, messages)

    def _perform_identifier_level_validations(
        self, document_type: type["Document"], api_client: "MarklogicApiClient"
    ) -> SuccessFailureMessageTuple:
        """Perform identifier validations at the individual identifier level."""

        success = True
        messages: list[str] = []

        for _, identifier in self.items():
            validations = identifier.perform_all_validations(document_type=document_type, api_client=api_client)
            if validations.success is False:
                success = False

            messages += validations.messages

        return SuccessFailureMessageTuple(success, messages)

    def perform_all_validations(
        self, document_type: type["Document"], api_client: "MarklogicApiClient"
    ) -> SuccessFailureMessageTuple:
        """Perform all possible identifier validations on this collection, both at the individual and collection level."""

        identifier_level_success, identifier_level_messages = self._perform_identifier_level_validations(
            document_type=document_type, api_client=api_client
        )
        collection_level_success, collection_level_messages = self._perform_collection_level_validations()

        success = all([identifier_level_success, collection_level_success])
        all_messages = identifier_level_messages + collection_level_messages

        return SuccessFailureMessageTuple(success, all_messages)

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

    def should_merge_one(self, identifier: Identifier) -> Identifier | None:
        # Is there a matching identifier (type and value) in the target? If so, disregard this source identifier
        # TODO: should this check for non-deprecation?
        if self.contains(identifier):
            return None

        # If the identifier doesn't match and the source identifier is deprecated, copy it over. Multiple deprecated identifiers are fine for all types.
        if identifier.deprecated:
            return identifier

        # If the source identifier isn't deprecated, does this identifier type support multiple current (ie non-deprecated) identifiers? If so, copy the source identifier into the target identifiers
        if identifier.schema.allow_multiple:
            return identifier

        # 4. If the existing identifier type doesn't support multiple current identifiers, deprecate the existing current one and copy the source identifier over
        identifier.deprecated = True
        return identifier

    def merge_logic(self, source: "IdentifiersCollection") -> "IdentifiersCollection":
        """
        Return an IdentifiersCollection suitable for replacing the 'self' IdentifiersCollection
        when 'other' is being merged into it. Getting the identifiers and saving them is the
        responsibility of a Document.
        """

        # should probably work on a copy of self, not self itself.
        source_identifiers: list[Identifier] = list(source.values())
        for identifier in source_identifiers:
            # Is there a matching identifier (type and value) in the target? If so, disregard this source identifier
            if self.should_merge_one(identifier):
                self.add(identifier)
        identifier.deprecated
        return self

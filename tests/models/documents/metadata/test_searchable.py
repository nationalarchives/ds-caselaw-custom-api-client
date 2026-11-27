from caselawclient.models.documents.metadata.searchable import (
    SEARCHABLE_METADATA_PROPERTY,
    build_searchable_metadata_etree,
)


def test_builds_one_judge_element_per_name():
    root = build_searchable_metadata_etree(["Lord Reed", "Sir Andrew McFarlane"])

    assert root.tag == SEARCHABLE_METADATA_PROPERTY
    assert [judge.text for judge in root] == ["Lord Reed", "Sir Andrew McFarlane"]


def test_no_judges_gives_an_empty_property():
    root = build_searchable_metadata_etree([])

    assert root.tag == SEARCHABLE_METADATA_PROPERTY
    assert len(root) == 0

from pathlib import Path

from ds_caselaw_utils.courts import courts
from jinja2 import StrictUndefined, Template
from typing_extensions import TypedDict


class PartyData(TypedDict):
    role: str  # Claimant or Defendant
    name: str


class EditorStubData(TypedDict):
    decision_date: str  # day precision
    transform_datetime: str  # second precision
    court_code_upper: str  # should be populated from court_code_
    title: str
    year: str
    case_numbers: list[str]  # can be none
    parties: list[PartyData]  # (type (claimant|defendant), name)


class RenderStubData(EditorStubData):
    court_code_lower: str
    court_url: str  # should be populated from utils/courts.cs
    court_full_name: str  # ditto


def add_other_stub_fields(editor_data: EditorStubData) -> RenderStubData:
    court = courts.get_court_by_code(editor_data["court_code_upper"])
    return {
        **editor_data,
        "court_code_lower": editor_data["court_code_upper"].lower(),
        # TODO: look up in utils
        "court_url": court.identifier_iri,
        "court_full_name": court.long_name,
    }


def create_stub(editor_data: EditorStubData) -> bytes:
    render_data = add_other_stub_fields(editor_data)
    from caselawclient.Client import ROOT_DIR

    judgment_path = Path(ROOT_DIR) / "models" / "documents" / "templates" / "judgment.xml"

    with (judgment_path).open("r") as f:
        template = f.read()

    rendered = bytes(Template(template, undefined=StrictUndefined).render(render_data).encode("utf-8"))

    return rendered

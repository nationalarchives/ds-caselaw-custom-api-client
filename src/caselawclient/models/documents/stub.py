from pathlib import Path
from typing import Literal

from ds_caselaw_utils.courts import courts
from ds_caselaw_utils.types import CourtCode
from jinja2 import StrictUndefined, Template
from typing_extensions import TypedDict


class PartyData(TypedDict):
    role: Literal["Claimant", "Respondent", "Appellant", "Defendant"]
    name: str


class EditorStubData(TypedDict):
    decision_date: str  # day precision
    transform_datetime: str  # second precision
    court_code: str
    title: str
    year: str
    case_numbers: list[str]  # can be none
    parties: list[PartyData]  # (type (claimant|defendant), name)


class RendererStubData(EditorStubData):
    court_url: str  # should be populated from utils/courts.cs
    court_full_name: str  # ditto


def add_other_stub_fields(editor_data: EditorStubData) -> RendererStubData:
    court = courts.get_court_by_code(CourtCode(editor_data["court_code"].upper()))
    return {
        **editor_data,
        "court_url": court.identifier_iri,
        "court_full_name": court.long_name,
    }


def render_stub_xml(editor_data: EditorStubData) -> bytes:
    render_data = add_other_stub_fields(editor_data)
    from caselawclient.Client import ROOT_DIR

    judgment_path = Path(ROOT_DIR) / "models" / "documents" / "templates" / "judgment.xml"

    with (judgment_path).open("r") as f:
        template = f.read()

    rendered = bytes(Template(template, undefined=StrictUndefined).render(render_data).encode("utf-8"))

    return rendered

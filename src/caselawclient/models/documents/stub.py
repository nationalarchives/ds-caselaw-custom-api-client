import os
from pathlib import Path
from typing import Literal, cast

from ds_caselaw_utils.courts import courts
from ds_caselaw_utils.types import CourtCode
from jinja2 import StrictUndefined, Template
from saxonche import PySaxonProcessor
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


def render_stub_xml_old(editor_data: EditorStubData) -> bytes:
    render_data = add_other_stub_fields(editor_data)
    from caselawclient.Client import ROOT_DIR

    judgment_path = Path(ROOT_DIR) / "models" / "documents" / "templates" / "judgment.xml"

    with (judgment_path).open("r") as f:
        template = f.read()

    rendered = bytes(Template(template, undefined=StrictUndefined).render(render_data).encode("utf-8"))

    return rendered


def render_stub_xml(editor_data: EditorStubData) -> bytes:
    render_data = add_other_stub_fields(editor_data)
    xquery_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates", "judgment.xqy")

    with PySaxonProcessor() as proc:
        xquery = proc.new_xquery_processor()
    xquery.set_query_file(file_name=xquery_location)

    xquery.set_parameter("decision_date", proc.make_string_value(render_data["decision_date"]))
    xquery.set_parameter("transform_datetime", proc.make_string_value(render_data["transform_datetime"]))
    xquery.set_parameter("court_code", proc.make_string_value(render_data["court_code"]))
    xquery.set_parameter("title", proc.make_string_value(render_data["title"]))
    xquery.set_parameter("year", proc.make_string_value(render_data["year"]))
    xquery.set_parameter("court_url", proc.make_string_value(render_data["court_url"]))
    xquery.set_parameter("court_full_name", proc.make_string_value(render_data["court_full_name"]))
    xquery.set_parameter(
        "case_numbers", proc.make_array([proc.make_string_value(x) for x in render_data["case_numbers"]])
    )

    builder = []
    for party in render_data["parties"]:
        builder.append(
            proc.make_map({proc.make_string_value(key): proc.make_string_value(value) for key, value in party.items()})
        )

    xquery.set_parameter("parties", proc.make_array(builder))
    return cast(bytes, xquery.run_query_to_string().encode("utf-8"))

from pathlib import Path

from jinja2 import Template
from typing_extensions import TypedDict


class PartyData(TypedDict):
    role: str  # Claimant or Defendant
    name: str


class StubData(TypedDict):
    decision_date: str  # day precision
    transform_datetime: str  # second precision
    court_code_upper: str
    court_code_lower: str  # should be populated from court_code_
    title: str
    court_url: str  # should be populated from utils/courts.cs
    court_full_name: str  # ditto
    year: str
    case_number: list[str]  # can be none
    parties: list[PartyData]  # (type (claimant|defendant), name)


def create_stub(data: StubData) -> bytes:
    from caselawclient.Client import ROOT_DIR

    judgment_path = Path(ROOT_DIR) / "models" / "documents" / "templates" / "judgment.xml"

    with (judgment_path).open("r") as f:
        template = f.read()

    rendered = bytes(Template(template).render(data).encode("utf-8"))

    return rendered

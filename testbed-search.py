import environ

env = environ.Env()

print(env("MARKLOGIC_HOST"))
from src.caselawclient import Client
from src.caselawclient.Client import MarklogicApiClient, api_client

response = api_client.do_bad_search(
    {
        "page": 1,
        "page-size": 10,
        "q": "",
        "party": "",
        "court": None,
        "judge": "",
        "neutral_citation": "",
        "specific_keyword": "",
        "order": "",
        "from": "",
        "to": "",
        "show_unpublished": "true",
        "only_unpublished": "false",
        "editor_status": "",
        "editor_priority": "30",
        "editor_assigned": "",
    }
)
print(response)

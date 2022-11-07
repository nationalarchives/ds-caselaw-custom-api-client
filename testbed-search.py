import environ

env = environ.Env()

from src.caselawclient.Client import api_client

print(env("MARKLOGIC_HOST"))

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
        "editor_status": "",  # not implemented
        "editor_priority": "",  # 10 has 2 records
        "editor_assigned": "admin",  # admin has 5 records
    }
)
print(response)

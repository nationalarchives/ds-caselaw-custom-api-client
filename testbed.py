import environ

env = environ.Env()

print(env("MARKLOGIC_HOST"))
from src.caselawclient import Client
from src.caselawclient.Client import MarklogicApiClient, api_client

response = api_client.get_properties_for_search_results(
    [
        "ukut/lc/2022/241",
        "ewhc/scco/2022/2562",
        "ewhc/ch/2022/2552",
    ]
)
print(response)

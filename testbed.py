import environ

env = environ.Env()

from src.caselawclient.Client import api_client

print(env("MARKLOGIC_HOST"))

response = api_client.get_properties_for_search_results(
    [
        "ukut/lc/2022/241",
        "ewhc/scco/2022/2562",
        "ewhc/ch/2022/2552",
    ]
)
print(response)

from caselawclient.Client import (
    MarklogicApiClient,
)

from caselawclient.models.judgments import Judgment
import os
from dotenv import load_dotenv
import timeit

load_dotenv()  # reads variables from a .env file and sets them in os.environ

MARKLOGIC_HOST = os.environ.get("MARKLOGIC_HOST")
MARKLOGIC_USER = os.environ.get("MARKLOGIC_USER")
MARKLOGIC_PASSWORD = os.environ.get("MARKLOGIC_PASSWORD")

client = MarklogicApiClient(MARKLOGIC_HOST, MARKLOGIC_USER, MARKLOGIC_PASSWORD, False)

last_200 = '="mark_729">a</uk:mark> false explanation of the transfer.</span></p>\n\t      </content>\n\t    </subparagraph>\n\t  </paragraph>\n\t</level>\n      </decision>\n    </judgmentBody>\n  </judgment>\n</akomaNtoso>'

def get_judgment():
    judgment= Judgment("ewhc/ch/2024/505", api_client=client, search_query="a "*100)
    assert "mark_729" in judgment.body.content_as_xml[-200:], judgment.body.content_as_xml[-200:]
    assert "mark_729" in judgment.body.content_as_xml
    assert "mark_730" not in judgment.body.content_as_xml
    # breakpoint()

def get_judgment_all():
    judgment= Judgment("ewhc/ch/2024/505", api_client=client, search_query="to")
    

def test_speed():
    speed = (timeit.timeit(get_judgment_all, number=1))
    assert speed < 0 

    # running it with "a "*X is Y seconds
    # X < 10, Y=3
    # X = 50, Y=4
    # X = 100, Y=6
    # X = 130, Y=8.4

    # "q "*5000 is 2 seconds.

    # "a the an of no" routinely times out
    # "to" is 6 to 9 seconds.



    
    
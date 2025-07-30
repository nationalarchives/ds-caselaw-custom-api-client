from caselawclient.factories import DocumentBodyFactory, DocumentFactory


class TestAttributeCompare:
    def test_compare_identical(self):
        this_doc = DocumentFactory.build()
        that_doc = DocumentFactory.build()
        comparisons = this_doc.compare_to(that_doc)
        for item in comparisons:
            assert item["match"]
        assert comparisons.match()

    def test_compare_different(self):
        this_doc = DocumentFactory.build()
        that_doc = DocumentFactory.build(
            body=DocumentBodyFactory.build(name="Different", court="Different", document_date_as_string="2000-01-09")
        )
        comparisons = this_doc.compare_to(that_doc)

        for item in comparisons:
            assert not item["match"]
        assert not comparisons.match()

        assert comparisons.get("name")["this_value"] == "Judgment v Judgement"
        assert comparisons.get("date")["this_value"] == "2023-02-03"
        assert comparisons.get("court")["this_value"] == "Court of Testing"

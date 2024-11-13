xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";

declare variable $parent_uri as xs:string external;
declare variable $component as xs:string external;

let $collectionQuery := cts:collection-query(("http://marklogic.com/collections/dls/latest-version"))
let $docTypeQuery := cts:element-attribute-value-query(
      xs:QName("akn:doc"),
      xs:QName("name"),
      $component
    )
let $refQuery := cts:element-query(
      xs:QName("uk:summaryOf"),
      concat("https://caselaw.nationalarchives.gov.uk/id/", $parent_uri)
    )

return xdmp:node-uri(cts:search(//akn:akomaNtoso, cts:and-query(($refQuery, $collectionQuery, $docTypeQuery))))

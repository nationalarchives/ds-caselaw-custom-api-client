xquery version "1.0-ml";

declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";
declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare variable $uri as xs:string external;

let $judgment := fn:document($uri)

return $judgment/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary/uk:court/text()
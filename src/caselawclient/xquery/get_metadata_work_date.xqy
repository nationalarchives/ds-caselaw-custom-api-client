xquery version "1.0-ml";

declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";
declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare variable $uri as xs:string external;

let $judgment := fn:document($uri)
let $date_element := $judgment/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate
return if ($date_element/@name = "dummy") then () else ($date_element/@date)

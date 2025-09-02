xquery version "1.0-ml";
declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";
declare variable $uri as xs:string external;

let $doc := doc($uri)
let $hash := $doc//uk:hash/text()
let $count := count(cts:search(fn:doc(), cts:element-value-query(xs:QName("uk:hash"), $hash)))
return $count = 1

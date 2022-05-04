xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";
declare variable $uri as xs:string external;
declare variable $content as xs:string external;

if (fn:boolean(
cts:search(doc($uri),
cts:element-query(xs:QName('uk:court'),cts:and-query(()))))) then
    xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary/uk:court,
    <uk:court>{$content}</uk:court>)
else
    xdmp:node-insert-child(
      document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary,
      <uk:court>{$content}</uk:court>
    )

xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";
declare variable $uri as xs:string external;
declare variable $content as xs:string external;

xdmp:node-replace(
document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary/uk:cite,
<uk:cite>{$content}</uk:cite>)

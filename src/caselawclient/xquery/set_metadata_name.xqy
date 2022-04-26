xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare variable $uri as xs:string external;
declare variable $content as xs:string external;

xdmp:node-replace(
document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname,
<akn:FRBRname value="{$content}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>)

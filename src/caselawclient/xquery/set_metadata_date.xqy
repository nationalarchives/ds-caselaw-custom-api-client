xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare variable $uri as xs:string external;
declare variable $content as xs:string external;

if (fn:boolean(
cts:search(doc($uri),
cts:element-query(xs:QName('akn:FRBRdate'),cts:and-query(()))))) then
    xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate,
    <akn:FRBRdate date="{$content}" name="judgment" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>)
else
    xdmp:node-insert-child(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork,
    <akn:FRBRdate date="{$content}" name="judgment" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    )

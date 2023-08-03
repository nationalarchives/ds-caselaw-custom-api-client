xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare variable $uri as xs:string external;
declare variable $content as xs:string external;

let $date_attr_name := doc($uri)/akn:akomaNtoso/akn:judgment/@name


let $work-date-node := doc($uri)/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate
let $expression-date-node := doc($uri)/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRExpression/akn:FRBRdate

(: https://github.com/nationalarchives/ds-find-caselaw-docs/blob/main/doc/adr/0008-how-frbrdates-are-managed.md :)
(: Keep these two dates in sync for now as per our ADR :)
return (
    xdmp:node-replace(
    $work-date-node,
    <akn:FRBRdate date="{$content}" name="{$date_attr_name}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>),

    xdmp:node-replace(
    $expression-date-node,
    <akn:FRBRdate date="{$content}" name="{$date_attr_name}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>)
)

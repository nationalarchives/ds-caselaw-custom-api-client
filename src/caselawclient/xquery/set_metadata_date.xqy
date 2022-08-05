xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare variable $uri as xs:string external;
declare variable $content as xs:string external;

(: If at least one FRBRWork/FRBRdate element exists then...:)
if (fn:boolean(
cts:search(doc($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork,
cts:element-query(xs:QName('akn:FRBRdate'),cts:and-query(()))))) then
    (: ...iterate over the FRBRdate element(s) :)
    for $frbr_date in doc($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate
        (: Store the existing @name attribute value :)
        let $attribute_name := $frbr_date/@name
        (: Replace the exisitng FRBRdate element with a new one, using the same @name attribute :)
        return xdmp:node-replace(
        document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate[@name = $attribute_name],
        <akn:FRBRdate date="{$content}" name="{$attribute_name}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>)
else
    (: No FRBRdate exists in FRBRWork, so create a new one and use the 'judgment' attribute name as default  :)
    xdmp:node-insert-child(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork,
    <akn:FRBRdate date="{$content}" name="judgment" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    )

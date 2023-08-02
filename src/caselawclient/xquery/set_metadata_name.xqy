xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare variable $uri as xs:string external;
declare variable $content as xs:string external;

declare function local:get-name-node($root-node)
{
  if ($root-node//akn:judgment) then
    $root-node//akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname
  else if ($root-node//akn:doc[@name = "pressSummary"]) then
    $root-node//akn:doc[@name = "pressSummary"]/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname
  else ()
};

let $doc := fn:doc($uri)
let $name-node := local:get-name-node($doc)

return if (fn:boolean(
cts:search(doc($uri),
cts:element-query(xs:QName('akn:FRBRname'),cts:and-query(()))))) then
    xdmp:node-replace(
    $name-node,
    <akn:FRBRname value="{$content}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    )
else
    xdmp:node-insert-child(
    $name-node,
    <akn:FRBRname value="{$content}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    )

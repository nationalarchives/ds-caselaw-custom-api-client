xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare variable $uri as xs:string external;
declare variable $content as xs:string external;

let $doc := fn:doc($uri)

let $work-node := $doc//akn:*/akn:meta/akn:identification/akn:FRBRWork
let $name-node := $work-node/akn:FRBRname

return if (fn:boolean(
cts:search(doc($uri),
cts:element-query(xs:QName('akn:FRBRname'),cts:and-query(()))))) then
    xdmp:node-replace(
      $name-node,
      <akn:FRBRname value="{$content}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    )
else
    xdmp:node-insert-child(
      $work-node,
      <akn:FRBRname value="{$content}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    )

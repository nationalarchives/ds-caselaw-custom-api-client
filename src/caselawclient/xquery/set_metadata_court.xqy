xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";

declare variable $uri as xs:string external;
declare variable $content as xs:string external;
declare variable $proprietary-node := document($uri)/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary;
declare variable $court-node := $proprietary-node/uk:court;

declare function local:delete($uri)
{
   xdmp:node-delete($court-node)
};

declare function local:edit($uri, $content)
{
   xdmp:node-replace(
      $court-node,
     <uk:court>{$content}</uk:court>
   )
};

declare function local:add($uri, $content)
{
   xdmp:node-insert-child(
     $proprietary-node,
     <uk:court>{$content}</uk:court>
   )
};

if (fn:boolean(
cts:search(doc($uri),
cts:element-query(xs:QName('uk:court'),cts:and-query(()))))) then
    if ($content = "") then local:delete($uri) else local:edit($uri, $content)
else
    local:add($uri, $content)

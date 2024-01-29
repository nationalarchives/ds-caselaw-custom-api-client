xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";

declare variable $uri as xs:string external;
declare variable $content as xs:string external;
declare variable $proprietary-node := document($uri)/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary;
declare variable $jurisdiction-node := $proprietary-node/uk:jurisdiction;

declare function local:delete($uri)
{
   xdmp:node-delete($jurisdiction-node)
};

declare function local:edit($uri, $content)
{
   xdmp:node-replace(
      $jurisdiction-node,
     <uk:jurisdiction>{$content}</uk:jurisdiction>
   )
};

declare function local:add($uri, $content)
{
   xdmp:node-insert-child(
     $proprietary-node,
     <uk:jurisdiction>{$content}</uk:jurisdiction>
   )
};

if (fn:boolean(
cts:search(doc($uri),
cts:element-query(xs:QName('uk:jurisdiction'),cts:and-query(()))))) then
    if ($content = "") then local:delete($uri) else local:edit($uri, $content)
else
    local:add($uri, $content)

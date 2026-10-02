xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $document as xs:string external;
declare variable $type_collection as xs:string external;
declare variable $annotation as xs:string external;

declare option xdmp:commit "explicit";
declare option xdmp:update "true";

let $document_xml := xdmp:unquote($document)

return dls:document-insert-and-manage(
  $uri,
  fn:true(),
  $document_xml,
  $annotation,
  (),
  ($type_collection)
);

(: The property write must see the managed document created by the first statement. :)
import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $properties as xs:string external;

let $updates := xdmp:unquote($properties)/properties/*
return (
  if (fn:exists($updates)) then dls:document-add-properties($uri, $updates) else (),
  xdmp:commit()
)

xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $document as xs:string external;
declare variable $type_collection as xs:string external;
declare variable $annotation as xs:string external;

let $document_xml := xdmp:unquote($document)

return dls:document-insert-and-manage(
  $uri,
  fn:true(),
  $document_xml,
  $annotation,
  (),
  ($type_collection)
)

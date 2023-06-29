xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $old_uri as xs:string external;
declare variable $new_uri as xs:string external;

let $document := fn:doc($old_uri)

let $collections :=
  if (fn:contains($new_uri, 'press-summary'))
  then ("press-summary")
  else ("judgment")

return dls:document-insert-and-manage($new_uri, fn:false(), $document, (), (), $collections)

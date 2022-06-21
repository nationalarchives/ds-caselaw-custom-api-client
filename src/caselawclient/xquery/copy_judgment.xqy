xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $old_uri as xs:string external;
declare variable $new_uri as xs:string external;

let $judgment := fn:doc($old_uri)

return dls:document-insert-and-manage($new_uri, fn:false(), $judgment)
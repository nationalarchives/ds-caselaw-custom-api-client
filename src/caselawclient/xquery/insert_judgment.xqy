xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $judgment as xs:string external;

let $judgment_xml := xdmp:unquote($judgment)

return dls:document-insert-and-manage($uri, fn:true(), $judgment_xml)

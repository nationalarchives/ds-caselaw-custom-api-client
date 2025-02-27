xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls"
      at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $judgment as xs:string external;
declare variable $annotation as xs:string external;

let $judgment_xml := xdmp:unquote($judgment)

return dls:document-update(
   $uri,
   $judgment_xml,
   $annotation,
   fn:true() (: retain history :)
)

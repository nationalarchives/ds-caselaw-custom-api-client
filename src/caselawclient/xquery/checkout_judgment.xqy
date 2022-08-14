xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $annotation as xs:string external;
declare variable $timeout as xs:unsignedInt* external;

let $expires := if (fn:empty($timeout)) then () else $timeout

return dls:document-checkout($uri, fn:true(), $annotation, $expires)
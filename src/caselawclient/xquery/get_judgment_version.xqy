xquery version "1.0-ml";

import module namespace dls="http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $version as xs:string external;

let $version_int := xs:int($version)

return dls:document-version($uri, $version_int)
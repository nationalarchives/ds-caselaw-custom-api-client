xquery version "1.0-ml";

import module namespace dls="http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;

dls:document-version-uris($uri)

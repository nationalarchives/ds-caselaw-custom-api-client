xquery version "1.0-ml";

import module namespace json="http://marklogic.com/xdmp/json" at "/MarkLogic/json/json.xqy";
declare variable $uri as xs:string external;

xdmp:document-get-properties($uri, xs:QName("history"))

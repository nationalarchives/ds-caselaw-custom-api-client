xquery version "1.0-ml";
declare namespace dls = "http://marklogic.com/xdmp/dls";
declare variable $uri as xs:string external;

let $annotation := xdmp:document-properties($uri)//dls:annotation/text()

return if (fn:exists($annotation)) then $annotation else ""

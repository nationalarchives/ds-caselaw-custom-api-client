xquery version "1.0-ml";
declare namespace dls = "http://marklogic.com/xdmp/dls";
declare variable $uri as xs:string external;

let $created := xdmp:document-properties($uri)//dls:created/text()

return if (fn:exists($created)) then $created else ""

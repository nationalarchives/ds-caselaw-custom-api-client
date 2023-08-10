xquery version "1.0-ml";

declare namespace xdmp = "http://marklogic.com/xdmp";

declare variable $uri as xs:string external;
declare variable $name as xs:string external;

let $prop := fn:QName("", $name)

return xdmp:document-get-properties($uri, $prop)/text()

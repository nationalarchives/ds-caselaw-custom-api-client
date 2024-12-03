xquery version "1.0-ml";

declare variable $uri as xs:string external;

declare variable $name as xs:string external;

let $prop := fn:QName("", $name)

return xdmp:document-get-properties($uri, $prop)

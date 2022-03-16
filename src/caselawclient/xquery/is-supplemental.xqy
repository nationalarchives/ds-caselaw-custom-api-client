xquery version "1.0-ml";

declare variable $uri as xs:string? external;

let $prop := fn:QName("","supplemental")

return xdmp:document-get-properties($uri, $prop)

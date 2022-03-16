xquery version "1.0-ml";

declare variable $uri as xs:string? external;

let $prop := fn:QName("","published")

return xdmp:document-get-properties($uri, $prop)/text()

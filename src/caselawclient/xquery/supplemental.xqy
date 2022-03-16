xquery version "1.0-ml";

declare variable $uri as xs:string? external;
declare variable $supplemental as xs:string? external;

let $props := ( <supplemental>{xs:boolean($supplemental)}</supplemental> )

return xdmp:document-set-properties($uri, $props)

xquery version "1.0-ml";

declare variable $uri as xs:string? external;
declare variable $published as xs:string? external;

let $props := ( <published>{xs:boolean($published)}</published> )

return xdmp:document-set-properties($uri, $props)

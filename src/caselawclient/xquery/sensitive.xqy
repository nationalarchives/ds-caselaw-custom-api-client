xquery version "1.0-ml";

declare variable $uri as xs:string? external;
declare variable $sensitive as xs:string? external;

let $props := ( <sensitive>{xs:boolean($sensitive)}</sensitive> )

return xdmp:document-set-properties($uri, $props)

xquery version "1.0-ml";

declare variable $uri as xs:string external;
declare variable $value as xs:string external;
declare variable $name as xs:string external;

let $props := ( element {$name}{xs:boolean($value)} )

return xdmp:document-set-properties($uri, $props)

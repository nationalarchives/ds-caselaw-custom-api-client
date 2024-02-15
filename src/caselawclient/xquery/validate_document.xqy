xquery version "1.0-ml";

declare variable $uri as xs:string external;

let $judgment := fn:document($uri)

return xdmp:validate($judgment)

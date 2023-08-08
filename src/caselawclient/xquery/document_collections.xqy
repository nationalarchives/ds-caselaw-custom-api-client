xquery version "1.0-ml";

declare variable $uri as xs:string external;

let $error := if (not(fn:doc-available($uri))) then (fn:error(xs:QName("FCL-DOCUMENTNOTFOUND"), "FCL-DOCUMENTNOTFOUND No document at "||$uri )) else ()
return xdmp:document-get-collections($uri)

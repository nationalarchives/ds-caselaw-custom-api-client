xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";
declare variable $uri as xs:string external;

let $_ := if (fn:not(fn:exists($uri))) then (fn:error(xs:QName("FCL-DOCUMENTNOTFOUND"), "No document at "||$uri)) else ()
let $xml := fn:document($uri)
let $external-uris := $xml//akn:ref[@uk:isNeutral=fn:true()]/@href
let $ml-uris := for $uri in $external-uris return fn:concat(fn:replace($uri, ".*/id/", ""), ".xml")
let $list := for $uri in $ml-uris return <cite href="{$uri}" available="{fn:doc-available($uri)}"/>
(: fn:doc-available(@uri) :)
return <x>{$list}</x>
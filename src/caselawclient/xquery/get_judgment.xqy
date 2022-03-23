xquery version "1.0-ml";

declare variable $show_unpublished as xs:boolean? external;
declare variable $uri as xs:string external;
declare variable $version_uri as xs:string? external;

let $judgment := fn:document($uri)
let $version := if ($version_uri) then fn:document($version_uri) else ()
let $judgment_published_property := xdmp:document-get-properties($uri, xs:QName("published"))[1]
let $is_published := $judgment_published_property/text()

let $document_to_return := if ($version_uri) then $version else $judgment

let $return_value := if ($show_unpublished) then
        $document_to_return
    else if (xs:boolean($is_published)) then
        $document_to_return
    else
        ()

return $return_value
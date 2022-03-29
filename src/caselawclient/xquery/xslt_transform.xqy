xquery version "1.0-ml";

declare variable $show_unpublished as xs:boolean? external;
declare variable $uri as xs:string external;
declare variable $version_uri as xs:string? external;

let $judgment_xml := fn:doc($uri)
let $version_xml := if ($version_uri) then fn:document($version_uri) else ()
let $judgment_published_property := xdmp:document-get-properties($uri, xs:QName("published"))[1]
let $is_published := $judgment_published_property/text()

let $document_to_transform := if ($version_xml) then $version_xml else $judgment_xml

let $return_value := if (xs:boolean($is_published) or $show_unpublished) then
        xdmp:xslt-invoke('judgments/xslts/judgment2.xsl',
          $document_to_transform
        )/element()
    else
        ()

return $return_value
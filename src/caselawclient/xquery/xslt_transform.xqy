xquery version "1.0-ml";

declare variable $show_unpublished as xs:boolean? external;
declare variable $uri as xs:string external;
declare variable $version_uri as xs:string? external;
declare variable $img_location as xs:string? external;
declare variable $xsl_filename as xs:string? external;

let $judgment_xml := fn:doc($uri)
let $version_xml := if ($version_uri) then fn:document($version_uri) else ()
let $judgment_published_property := xdmp:document-get-properties($uri, xs:QName("published"))[1]
let $is_published := $judgment_published_property/text()
let $image_base := if ($img_location) then $img_location else ""
let $xsl := if ($xsl_filename) then $xsl_filename else "judgment2.xsl"

let $document_to_transform := if ($version_xml) then $version_xml else $judgment_xml
let $xsl_path := fn:concat("judgments/xslts/", $xsl)

let $params := map:map()
let $_put := map:put(
                    $params,
                    "image-base",
                    $image_base)

let $return_value := if (xs:boolean($is_published) or $show_unpublished) then
        xdmp:xslt-invoke($xsl_path,
          $document_to_transform,
          $params
        )/element()
    else
        ()

return $return_value
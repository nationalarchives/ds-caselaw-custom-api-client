xquery version "1.0-ml";

declare variable $show_unpublished as xs:boolean? external;
declare variable $uri as xs:string external;
declare variable $version_uri as xs:string? external;
declare variable $img_location as xs:string? external;
declare variable $xsl_filename as xs:string? external;

let $judgment_published_property := xdmp:document-get-properties($uri, xs:QName("published"))[1]
let $is_published := $judgment_published_property/text()
let $image_base := if ($img_location) then $img_location else ""
let $document_to_transform := if ($version_uri) then fn:document($version_uri) else fn:doc($uri)
let $xsl_path := fn:concat("judgments/xslts/", $xsl_filename)

let $params := map:map()

(: change the image-base of the document to match the location of the assets in $image_base
   so that references to images point to the correct places on the internet :)
let $_put := map:put(
                    $params,
                    "image-base",
                    $image_base)

let $_ := if (not(exists($document_to_transform))) then
  (
    fn:error(xs:QName("FCL_DOCUMENTNOTFOUND"), "No XML document was found to transform")
  ) else ()

let $return_value := if (xs:boolean($is_published) or $show_unpublished) then
        xdmp:xslt-invoke($xsl_path,
          $document_to_transform,
          $params
        )/element()
    else
        ()

return $return_value

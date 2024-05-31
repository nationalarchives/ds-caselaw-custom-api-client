xquery version "1.0-ml";

import module namespace helper = "https://caselaw.nationalarchives.gov.uk/helper" at "/judgments/search/helper.xqy";
declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";

declare variable $show_unpublished as xs:boolean? external;
declare variable $uri as xs:string external;
declare variable $version_uri as xs:string? external;
declare variable $img_location as xs:string? external;
declare variable $xsl_filename as xs:string? external;
declare variable $query as xs:string? external;

declare function local:public-to-marklogic($uri as xs:string) as xs:string
{
  (: inspired by https://stackoverflow.com/questions/27745/getting-parts-of-a-url-regex :)
  (: https://caselaw.nationalarchives.gov.uk/uksc/2024/1 -> /uksc/2024/1.xml :)
  fn:replace($uri, "^.*//[^/]*", "")||".xml"
};

declare function local:marklogic-to-public($uri as xs:string) as xs:string
{
  "https://caselaw.nationalarchives.gov.uk/"||fn:replace($uri, ".xml$", "")
};

declare function local:get-linked-caselaw($source-uri as xs:string) (: as returnDatatype:)
{
  let $xml := fn:document($source-uri)
  let $external-uris := $xml//akn:ref[@uk:isNeutral=fn:true()]/@href
  let $ml-uris := for $uri in $external-uris return local:public-to-marklogic($uri)
  let $list := for $uri in $ml-uris return <cite href="{$uri}" available="{fn:doc-available($uri)}"/>
  (: fn:doc-available(@uri) :)
  return $list
};

let $judgment_published_property := xdmp:document-get-properties($uri, xs:QName("published"))[1]
let $is_published := $judgment_published_property/text()
let $image_base := if ($img_location) then $img_location else ""
let $document_to_transform := if ($version_uri) then fn:document($version_uri) else fn:doc($uri)
let $xsl_path := fn:concat("judgments/xslts/", $xsl_filename)

let $params := map:map()

let $number_marks_xslt := (
  <xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                  version="2.0">
    <xsl:output method="html" />
    <xsl:template match="@*|node()">
      <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
      </xsl:copy>
    </xsl:template>
    <xsl:template match="mark">
      <xsl:copy>
          <xsl:copy-of select="@*" />
          <xsl:attribute name="id">
              <xsl:text>mark_</xsl:text>
              <xsl:value-of select="count(preceding::mark)"/>
          </xsl:attribute>
          <xsl:apply-templates />
      </xsl:copy>
    </xsl:template>
  </xsl:stylesheet>
)
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

let $retrieved_value := if (xs:boolean($is_published) or $show_unpublished) then
        xdmp:xslt-invoke($xsl_path,
          $document_to_transform,
          $params
        )/element()
    else
        ()

let $return_value := if($query) then
      xdmp:xslt-eval(
        $number_marks_xslt,
        cts:highlight(
          $retrieved_value,
          helper:make-q-query($query),
          <mark>{$cts:text}</mark>
        )
      )
    else
      $retrieved_value

return $return_value
(: return local:get-linked-caselaw($uri) :)
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
declare variable $DOMAIN := "https://caselaw.nationalarchives.gov.uk";

declare function local:public-to-marklogic($uri as xs:string) as xs:string
{
  (: inspired by https://stackoverflow.com/questions/27745/getting-parts-of-a-url-regex :)
  (: fn:replace($uri, "^.*//[^/]*", "")||".xml" :)
  (: https://caselaw.nationalarchives.gov.uk/uksc/2024/1 -> /uksc/2024/1.xml :)
  (: it's possible that just hardcoding the domain is a better approach, e.g. :)
  fn:replace($uri, "^" || $DOMAIN || "/", "/") || ".xml"
};

declare function local:marklogic-to-public($uri as xs:string) as xs:string
{
  $DOMAIN||fn:replace($uri, ".xml$", "")
};

declare function local:get-linked-caselaw($source-uri as xs:string) {
    (: Check to see if referenced caselaw in the source-uri document exists within the database
       return the full original URIs of documents that do. Requires sleight of hand to convert URIs
       from fully-qualified to marklogic URIs and back. :)
    let $_ := if (fn:not(fn:exists($uri))) then (fn:error(xs:QName("FCL-DOCUMENTNOTFOUND"), "No document at "||$uri)) else ()
    let $xml := fn:document($uri)
    let $external-uris := $xml//akn:ref[@uk:isNeutral=fn:true()]/@href
    let $ml-uris := for $uri in $external-uris return local:public-to-marklogic($uri)
    let $existing-caselaw-list := for $uri in $ml-uris where fn:doc-available($uri) return $uri
    return for $uri in $existing-caselaw-list return local:marklogic-to-public($uri)
};

let $judgment_published_property := xdmp:document-get-properties($uri, xs:QName("published"))[1]
let $is_published := $judgment_published_property/text()
let $image_base := if ($img_location) then $img_location else ""
let $document_to_transform := if ($version_uri) then fn:document($version_uri) else fn:doc($uri)
let $xsl_path := fn:concat("judgments/xslts/", $xsl_filename)

let $tag-existing-caselaw-transform :=  <xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                  xmlns:xs="http://www.w3.org/2001/XMLSchema"
                  xpath-default-namespace="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                  version="2.0">

    
    <xsl:param name="existingcaselaw" as="xs:string*" select="()" />

    <xsl:template match="ref">
      <xsl:variable name="exists" select="if(./@href=$existingcaselaw) then 'yes' else 'no'"/>
      <xsl:copy>
      
      <xsl:apply-templates select="@*"/> 
      <xsl:attribute name="exists">
        <xsl:value-of select="$exists" />
      </xsl:attribute>
      <xsl:apply-templates select="node()"/> 
      
      </xsl:copy>
    </xsl:template>

    <xsl:template match="@*|node()">
      <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
      </xsl:copy>
    </xsl:template>
  </xsl:stylesheet>

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
          <xsl:copy-of select="*" />
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

let $params := map:map()
let $_put := map:put(
                    $params,
                    "image-base",
                    $image_base)
let $_put2 := map:put(
                    $params,
                    "existingcaselaw",
                    local:get-linked-caselaw($uri))

let $_ := if (not(exists($document_to_transform))) then
  (
    fn:error(xs:QName("FCL_DOCUMENTNOTFOUND"), "No XML document was found to transform")
  ) else ()

(: go from document-to-transform and change all the ref tags :)
let $tagged_document := xdmp:xslt-eval(
        $tag-existing-caselaw-transform,
        $document_to_transform, 
        $params)

let $retrieved_value := if (xs:boolean($is_published) or $show_unpublished) then
        xdmp:xslt-invoke($xsl_path,
          $tagged_document,
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

return $tagged_document
xquery version "1.0-ml";

declare namespace xdmp = "http://marklogic.com/xdmp";
declare namespace cts = "http://marklogic.com/cts";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";
import module namespace helper = "https://caselaw.nationalarchives.gov.uk/helper" at "/judgments/search/helper.xqy";

declare variable $show_unpublished as xs:boolean? external;
declare variable $uri as xs:string external;
declare variable $version_uri as xs:string? external;
declare variable $search_query as xs:string? external;

(: Note that `xsl:output method` is changed from `html` to `xml` and we've namespaced the tag :)
let $number_marks_xslt := (
  <xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                  xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                  xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                  version="2.0">
    <xsl:output method="xml" />
    <xsl:template match="@*|node()">
      <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
      </xsl:copy>
    </xsl:template>
    <xsl:template match="//akn:meta//uk:mark">
          <xsl:apply-templates />
    </xsl:template>
    <xsl:template match="uk:mark">
      <xsl:copy>
          <xsl:copy-of select="@*" />
          <xsl:attribute name="id">
              <xsl:text>mark_</xsl:text>
              <xsl:number count="//uk:mark" level="any" from="//*[ancestor::akn:meta]" />
          </xsl:attribute>
          <xsl:apply-templates />
      </xsl:copy>
    </xsl:template>
  </xsl:stylesheet>
)

let $judgment := fn:document($uri)
let $version := if ($version_uri) then fn:document($version_uri) else ()
let $judgment_published_property := xdmp:document-get-properties($uri, xs:QName("published"))[1]
let $is_published := $judgment_published_property/text()

let $document_to_return := if ($version_uri) then $version else $judgment


let $raw_xml := if ($show_unpublished) then
        $document_to_return
    else if (xs:boolean($is_published)) then
        $document_to_return
    else
        ()

(: If a search query string is present, highlight instances :)
let $transformed := if($search_query) then
      xdmp:xslt-eval(
        $number_marks_xslt,
        cts:highlight(
          $raw_xml,
          helper:make-q-query($search_query),
          <uk:mark>{$cts:text}</uk:mark>
        )
      )
    else
      $raw_xml

return $transformed

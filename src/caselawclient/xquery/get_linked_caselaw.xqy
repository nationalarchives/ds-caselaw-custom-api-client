xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";
declare variable $DOMAIN := "https://caselaw.nationalarchives.gov.uk";
declare variable $uri as xs:string external;

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

let $params := map:map()
let $_put := map:put(
                    $params,
                    "existingcaselaw",
                    (: xdmp:key-from-QName(fn:QName("foo", "pName")), :)
                    local:get-linked-caselaw($uri))

let $foo-to-bar :=
  <xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                  xmlns:xs="http://www.w3.org/2001/XMLSchema"
                  xpath-default-namespace="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                  version="2.0">

    
    <xsl:param name="existingcaselaw" as="xs:string*" select="()" />

    <xsl:template match="ref">
      <xsl:variable name="exists" select="if(./@href=$existingcaselaw) then 'yes' else 'no'"/>
      <xsl:copy>
      
      <xsl:apply-templates select="@*"/> <!-- keep attributes --> 
      <xsl:attribute name="exists"> <!-- add whether it exists or not -->
        <xsl:value-of select="$exists" />
      </xsl:attribute>
      <xsl:apply-templates select="node()"/> <!-- keep children -->
      
      </xsl:copy>
    </xsl:template>

    <xsl:template match="@*|node()">
      <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
      </xsl:copy>
    </xsl:template>
  </xsl:stylesheet>


return 
xdmp:xslt-eval($foo-to-bar,
  fn:doc($uri),
  $params)

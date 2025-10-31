xquery version "1.0-ml";

declare namespace xdmp = "http://marklogic.com/xdmp";
declare namespace cts = "http://marklogic.com/cts";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";
import module namespace helper = "https://caselaw.nationalarchives.gov.uk/helper" at "/judgments/search/helper.xqy";

declare variable $show_unpublished as xs:boolean? external;
declare variable $uri as xs:string external;
declare variable $version_uri as xs:string? external;
declare variable $search_query as xs:string? external;

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
      cts:highlight(
        $raw_xml,
        helper:make-q-query($search_query),
        <uk:mark>{$cts:text}</uk:mark>
      )
    else
      $raw_xml

return $transformed

xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $version_number as xs:int external;
declare variable $annotation as xs:string external;

let $version_content := dls:document-version($uri, $version_number)

(: The caller must already hold the checkout (see Document.editing_session). Using
   dls:document-update rather than checkout-update-checkin keeps that checkout intact. :)
return dls:document-update(
  $uri,
  $version_content,
  $annotation,
  fn:true() (: retain history :)
)

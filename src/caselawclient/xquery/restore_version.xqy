xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $version_number as xs:int external;
declare variable $annotation as xs:string external;

let $version_content := dls:document-version($uri, $version_number)

return dls:document-checkout-update-checkin(
  $uri,
  $version_content,
  $annotation, 
  fn:true()
)

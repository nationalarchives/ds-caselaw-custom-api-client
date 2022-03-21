xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls"
      at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $judgment as node() external;
declare variable $annotation as xs:string external;

dls:document-checkout-update-checkin(
    $uri,
    $judgment,
    $annotation,
    fn:true()
)
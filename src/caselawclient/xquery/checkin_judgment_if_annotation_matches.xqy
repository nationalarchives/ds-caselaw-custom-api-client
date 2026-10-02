xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $annotation as xs:string external;

(: The ownership check and the check-in run in one update transaction, so a checkout
   taken by another session in between can never be checked in by mistake. :)
let $status := dls:document-checkout-status($uri)
return
  if (fn:exists($status) and fn:string($status/dls:annotation) eq $annotation)
  then (dls:document-checkin($uri, fn:true()), fn:true())
  else fn:false()

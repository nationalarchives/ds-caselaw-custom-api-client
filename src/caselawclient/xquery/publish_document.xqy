xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $properties as xs:string external;
declare variable $expected_state as xs:string external;

declare option xdmp:update "true";

let $_ := xdmp:lock-for-update($uri)
let $state := <state>{
  <properties>{xdmp:document-properties($uri)/*/*}</properties>,
  dls:document-history($uri)
}</state>
return
  if ($expected_state ne xdmp:sha256(xdmp:quote($state))) then
    fn:error(xs:QName("METRICS-STATE-CHANGED"), "Document changed while calculating metrics")
  else
    for $property in xdmp:unquote($properties)/properties/*
    return dls:document-set-property($uri, $property)

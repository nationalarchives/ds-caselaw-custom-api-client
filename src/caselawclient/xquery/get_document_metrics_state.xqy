xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;

let $state := <state>{
  <properties>{xdmp:document-properties($uri)/*/*}</properties>,
  dls:document-history($uri)
}</state>
return <state signature="{xdmp:sha256(xdmp:quote($state))}">{$state/*}</state>

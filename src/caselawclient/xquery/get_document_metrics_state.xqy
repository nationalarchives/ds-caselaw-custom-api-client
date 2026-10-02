xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;

<state>{
  <properties>{xdmp:document-properties($uri)/*/*}</properties>,
  dls:document-history($uri)
}</state>

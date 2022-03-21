xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls"
      at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;

declare variable $name as xs:string external;

let $prop := fn:QName("", $name)

return dls:document-get-properties($uri, $prop)/text()

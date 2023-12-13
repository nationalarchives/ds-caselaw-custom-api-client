xquery version "1.0-ml";

import module namespace json="http://marklogic.com/xdmp/json" at "/MarkLogic/json/json.xqy";
declare namespace basic="http://marklogic.com/xdmp/json/basic";
declare namespace flag="http://caselaw.nationalarchives.gov.uk/history/flags";

(: let $attributes := json:transform-from-json(xdmp:unquote('{"id": "3", "type": "telemetry", "service": "ingester"}'))
let $flags := json:transform-from-json(xdmp:unquote('["failed", "automated"]'))
let $payload := <payload><mice levels='3'>maurice</mice>kittens</payload>:)
declare variable $uri as xs:string external;
declare variable $attributes as json:object external;
declare variable $flags as json:array external;
declare variable $payload as xs:string external;

let $attributes-as-xml := json:transform-from-json($attributes)
let $flags-as-xml := json:transform-from-json($flags)
let $payload := xdmp:unquote($payload)

let $event := <event>
        {for $i in $attributes-as-xml/* return attribute {$i/name()} {$i/text()} }
        {attribute {"datetime"} {fn:current-dateTime()}}
        {for $i in $flags-as-xml//basic:item return attribute {fn:QName("http://caselaw.nationalarchives.gov.uk/history/flags", $i/text())} {"true"}}
        {$payload}
      </event>

let $history := xdmp:document-get-properties($uri, xs:QName("history"))

return if (fn:exists($history)) then
   xdmp:node-insert-child($history, $event)
else
   xdmp:document-set-property($uri, <history xmlns:flag="http://caselaw.nationalarchives.gov.uk/history/flags">{$event}</history>)

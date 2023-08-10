xquery version "1.0-ml";

declare namespace xdmp = "http://marklogic.com/xdmp";

declare variable $uri as xs:string external;

let $timestamp := xdmp:document-timestamp( $uri )

return xdmp:timestamp-to-wallclock( $timestamp )

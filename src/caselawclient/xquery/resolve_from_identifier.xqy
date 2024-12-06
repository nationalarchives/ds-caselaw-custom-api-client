xquery version "1.0-ml";

declare namespace xdmp="http://marklogic.com/xdmp"; 
declare variable $uri as xs:string external;

xdmp:sql(
  "SELECT * from compiled_url_slugs WHERE documents.compiled_url_slugs.identifier_slug = @uri",
  "array",
  map:new((
    map:entry("uri", $uri)
  ))
)

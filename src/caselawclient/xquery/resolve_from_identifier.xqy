xquery version "1.0-ml";

declare namespace xdmp="http://marklogic.com/xdmp"; 
declare variable $identifier_uri as xs:string external;

xdmp:sql(
  "SELECT * from compiled_url_slugs WHERE documents.compiled_url_slugs.identifier_slug = @uri",
  "map",
  map:new((
    map:entry("uri", $identifier_uri)
  ))
)

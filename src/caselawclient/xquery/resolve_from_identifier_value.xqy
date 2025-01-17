xquery version "1.0-ml";

declare namespace xdmp="http://marklogic.com/xdmp"; 
declare variable $identifier_value as xs:string external;
declare variable $published_only as xs:int? external := 1;

let $published_query := if ($published_only) then " AND document_published = 'true'" else ""
let $query := "SELECT * from compiled_url_slugs WHERE (identifier_value = @value)" ||  $published_query

return xdmp:sql(
  $query,
  "map",
  map:new((
    map:entry("value", $identifier_value)
  ))
)


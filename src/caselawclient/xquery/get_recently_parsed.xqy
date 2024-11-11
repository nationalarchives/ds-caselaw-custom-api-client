xquery version "1.0-ml";

declare namespace xdmp="http://marklogic.com/xdmp"; 
xdmp:to-json(xdmp:sql(
  "SELECT process_data.uri, hours_since_parse_request, parser_major_version, parser_minor_version
  FROM (
    SELECT 
      process_data.uri, parser_major_version, parser_minor_version,
      DATEDIFF('hour', last_sent_to_parser, CURRENT_TIMESTAMP) AS hours_since_parse_request
    FROM documents.process_data
    JOIN documents.process_property_data ON process_data.uri = process_property_data.uri
  )
  ORDER BY hours_since_parse_request ASC
  LIMIT 1000",
  "array",
  map:new((
  ))
))


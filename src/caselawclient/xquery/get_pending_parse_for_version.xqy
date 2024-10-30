xquery version "1.0-ml";

declare variable $target_major_version as xs:int external;
declare variable $target_minor_version as xs:int external;
declare variable $maximum_records as xs:int? external := 1000;

xdmp:to-json(xdmp:sql(
  "SELECT process_data.uri, parser_version_string, minutes_since_parse_request
  FROM (
    SELECT 
      process_data.uri,
      parser_version_string, parser_major_version, parser_minor_version,
      DATEDIFF('minute', last_sent_to_parser, CURRENT_TIMESTAMP) AS minutes_since_parse_request
    FROM documents.process_data
    JOIN documents.process_property_data ON process_data.uri = process_property_data.uri
  )
  WHERE (
    (parser_version_string IS NULL) OR
    (parser_major_version <= @target_major_version AND parser_minor_version < @target_minor_version)
  )
  AND (minutes_since_parse_request > 43200 OR minutes_since_parse_request IS NULL)
  ORDER BY parser_major_version ASC NULLS FIRST, parser_minor_version ASC
  LIMIT @maximum_records",
  "array",
  map:new((
    map:entry("target_major_version", $target_major_version),
    map:entry("target_minor_version", $target_minor_version),
    map:entry("maximum_records", $maximum_records)
    
  ))
))
xquery version "1.0-ml";

declare variable $target_enrichment_major_version as xs:int external;
declare variable $target_enrichment_minor_version as xs:int external;
declare variable $target_parser_major_version as xs:int external;
declare variable $target_parser_minor_version as xs:int external;

xdmp:to-json(xdmp:sql(
  "SELECT process_data.uri, enrich_version_string, minutes_since_enrichment_request
  FROM (
    SELECT
      process_data.uri,
      enrich_version_string, enrich_major_version, enrich_minor_version,
      parser_major_version, parser_minor_version,
      DATEDIFF('minute', last_sent_to_enrichment, CURRENT_TIMESTAMP) AS minutes_since_enrichment_request
    FROM documents.process_data
    JOIN documents.process_property_data ON process_data.uri = process_property_data.uri
  )
  WHERE (
    (enrich_version_string IS NULL) OR
    (enrich_major_version <= @target_enrichment_major_version AND enrich_minor_version < @target_enrichment_minor_version)
  ) AND (
    (parser_major_version = @target_parser_major_version AND parser_minor_version = @target_parser_minor_version)
  )
  AND (minutes_since_enrichment_request > 43200 OR minutes_since_enrichment_request IS NULL)
  ORDER BY enrich_major_version ASC NULLS FIRST, enrich_minor_version ASC",
  "array",
  map:new((
    map:entry("target_enrichment_major_version", $target_enrichment_major_version),
    map:entry("target_enrichment_minor_version", $target_enrichment_minor_version),
    map:entry("target_parser_major_version", $target_parser_major_version),
    map:entry("target_parser_minor_version", $target_parser_minor_version)
  ))
))


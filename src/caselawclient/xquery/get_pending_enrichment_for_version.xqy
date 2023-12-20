xquery version "1.0-ml";

declare variable $target_version as xs:int external;

xdmp:to-json(xdmp:sql(
  "SELECT process_data.uri, enrich_version_string, minutes_since_enrichment_request
  FROM (
    SELECT process_data.uri, enrich_version_string, enrich_major_version, DATEDIFF('minute', last_sent_to_enrichment, CURRENT_TIMESTAMP) AS minutes_since_enrichment_request
    FROM documents.process_data
    JOIN documents.process_property_data ON process_data.uri = process_property_data.uri
  )
  WHERE ((enrich_version_string IS NULL) OR (enrich_major_version < @target_version))
  AND (minutes_since_enrichment_request > 43200 OR minutes_since_enrichment_request IS NULL)
  ORDER BY enrich_major_version ASC NULLS FIRST",
  "array",
  map:new(map:entry("target_version", $target_version))
))


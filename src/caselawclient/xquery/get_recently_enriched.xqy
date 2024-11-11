xquery version "1.0-ml";

declare namespace xdmp="http://marklogic.com/xdmp"; 
xdmp:to-json(xdmp:sql(
  "SELECT *, process_data.uri, hours_since_enrichment_request, enrich_major_version, enrich_minor_version
  FROM (
    SELECT 
      process_data.uri, enrich_major_version, enrich_minor_version,
      DATEDIFF('hour', last_sent_to_enrichment, CURRENT_TIMESTAMP) AS hours_since_enrichment_request
    FROM documents.process_data
    JOIN documents.process_property_data ON process_data.uri = process_property_data.uri
  )
  ORDER BY hours_since_enrichment_request ASC
  LIMIT 1000",
  "array",
  map:new((
  ))
))
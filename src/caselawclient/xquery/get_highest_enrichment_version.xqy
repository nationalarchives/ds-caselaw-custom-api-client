xquery version "1.0-ml";

xdmp:to-json(xdmp:sql(
  "SELECT enrich_version_string, enrich_major_version, enrich_minor_version
   FROM documents.process_data
   ORDER BY enrich_major_version DESC, enrich_minor_version DESC
   LIMIT 1",
  "array"
))

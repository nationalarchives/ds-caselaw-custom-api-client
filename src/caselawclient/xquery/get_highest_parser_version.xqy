xquery version "1.0-ml";

xdmp:to-json(xdmp:sql(
  "SELECT parser_version_string, parser_major_version, parser_minor_version
   FROM documents.process_data
   ORDER BY parser_major_version DESC, parser_minor_version DESC
   LIMIT 1",
  "array"
))

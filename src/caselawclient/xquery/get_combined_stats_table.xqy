xquery version "1.0-ml";

xdmp:to-json(xdmp:sql(
  "SELECT
  documents.summary.uri AS version_uri,
  CASE
    WHEN documents.propertysummary.doc_uri IS NOT NULL
      THEN documents.propertysummary.doc_uri
    ELSE
      version_uri
  END AS document_uri,
  documents.summary.ncn AS neutral_citation,
  documents.summary.name AS name,
  documents.propertysummary.published AS published,
  documents.propertysummary.version_number as version_sequence_number,
  documents.propertysummary.modified AS last_modified
  FROM documents.summary
  JOIN documents.propertysummary
  ON documents.summary.uri = documents.propertysummary.uri
  ORDER BY document_uri, version_sequence_number",
  "array"
))


xquery version "1.0-ml";

declare variable $uris as json:array external;
let $properties := (
    fn:QName("", 'editor-priority'),
    fn:QName("", 'assigned-to'),
    fn:QName("", 'editor-hold'),
    fn:QName("", 'source-name'),
    fn:QName("", 'source-email'),
    fn:QName("", 'transfer-consignment-reference'),
    fn:QName("", 'transfer-received-at'),
    fn:QName("", 'published'),
    fn:QName("", 'email-received-at'),
    fn:QName("", 'metadata_fields')
)

return <property-results>{
for $uri in json:array-values($uris)
  let $timestamp := xdmp:document-timestamp($uri)
  return <property-result uri='{$uri}' last-modified='{if (fn:exists($timestamp)) then xdmp:timestamp-to-wallclock($timestamp) else ()}'> {
    for $prop in $properties
      return xdmp:document-get-properties($uri, $prop)
  } </property-result>
}</property-results>

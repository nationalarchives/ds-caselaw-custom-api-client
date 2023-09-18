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
    fn:QName("", 'published')
)

return <property-results>{
for $uri in json:array-values($uris)
  return <property-result uri='{$uri}'> {
    for $prop in $properties
      return xdmp:document-get-properties($uri, $prop)
  } </property-result>
}</property-results>

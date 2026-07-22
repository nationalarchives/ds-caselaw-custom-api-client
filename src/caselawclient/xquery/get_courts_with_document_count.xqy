xquery version "1.0-ml";

declare namespace cts = "http://marklogic.com/cts";
declare namespace map = "http://marklogic.com/xdmp/map";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";

let $query := cts:and-query((
  cts:collection-query("http://marklogic.com/collections/dls/latest-version"),
  cts:properties-fragment-query(
    cts:element-value-query(xs:QName("published"), "true")
  )
))
let $court-counts := map:map()
let $_ := (
  for $doc in cts:search(fn:collection(), $query)
  let $court-key := fn:lower-case(fn:normalize-space(fn:string(($doc//uk:court)[1])))
  let $existing-count := (map:get($court-counts, $court-key), 0)[1]
  where $court-key
  return map:put($court-counts, $court-key, $existing-count + 1)
)

return xdmp:to-json($court-counts)

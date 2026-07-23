xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn";

let $query := cts:and-query((
  dls:documents-query(),
  cts:properties-fragment-query(
    cts:element-value-query(fn:QName("", "published"), "true")
  )
))
let $court-ref := cts:path-reference(
  "//akn:proprietary/uk:court",
  ("type=string", "collation=http://marklogic.com/collation/")
)
let $court-counts := map:map()
let $_ := (
  for $court in cts:values($court-ref, (), ("item-order"), $query)
  let $court-key := fn:lower-case(fn:normalize-space($court))
  let $existing-count := (map:get($court-counts, $court-key), 0)[1]
  where $court-key
  return map:put($court-counts, $court-key, $existing-count + cts:frequency($court))
)
return xdmp:to-json($court-counts)
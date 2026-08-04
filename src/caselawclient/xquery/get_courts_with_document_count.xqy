xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare function local:canonical-court-param($court-param as xs:string) as xs:string {
  let $court-param := fn:replace($court-param, "^(ewca|ewhc|ukut|ukftt|ftt)-", "$1/")
  return
  if ($court-param = "ewhc/qb") then
    "ewhc/kb"
  else if ($court-param = "ewhc/costs") then
    "ewhc/scco"
  else if ($court-param = "ukait") then
    "ukut/iac"
  else
    $court-param
};

let $query := cts:and-query((
  cts:collection-query("judgment"),
  dls:documents-query(),
  cts:properties-fragment-query(
    cts:element-value-query(xs:QName("published"), "true")
  )
))
let $court-counts := map:map()
let $_ := (
  for $court in cts:element-values(xs:QName("uk:court"), (), ("item-order"), $query)
  let $court-key := local:canonical-court-param(fn:lower-case(fn:normalize-space($court)))
  let $existing-count := (map:get($court-counts, $court-key), 0)[1]
  where $court-key
  return map:put($court-counts, $court-key, $existing-count + cts:frequency($court))
)
return xdmp:to-json($court-counts)

xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";

declare function local:is-year($value as xs:string?) as xs:boolean {
  fn:matches(fn:string($value), "^[0-9]{4}$")
};

declare function local:canonical-court-param($court-param as xs:string) as xs:string {
  if ($court-param = "ewhc/qb") then
    "ewhc/kb"
  else if ($court-param = "ewhc/costs") then
    "ewhc/scco"
  else if ($court-param = "ukait") then
    "ukut/iac"
  else
    $court-param
};

declare function local:court-param-from-uri($uri as xs:string) as xs:string? {
  let $parts := fn:tokenize($uri, "/")[. ne ""]
  let $court := $parts[1]
  let $sub-court := $parts[2]
  let $court-param :=
    if (fn:empty($court)) then
      ()
    else if (
      $court = ("ewca", "ewhc", "ukut", "ukftt", "ftt")
      and fn:exists($sub-court)
      and fn:not(local:is-year($sub-court))
    ) then
      fn:concat($court, "/", $sub-court)
    else
      $court
  return
    if (fn:empty($court-param)) then
      ()
    else
      local:canonical-court-param($court-param)
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
  for $uri in cts:uris("", (), $query)
  let $court-key := local:court-param-from-uri($uri)
  let $existing-count := (map:get($court-counts, $court-key), 0)[1]
  where $court-key
  return map:put($court-counts, $court-key, $existing-count + 1)
)
return xdmp:to-json($court-counts)

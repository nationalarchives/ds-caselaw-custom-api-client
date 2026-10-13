xquery version "1.0-ml";

import module namespace filters = "https://caselaw.nationalarchives.gov.uk/search/filters" at "/judgments/search/filters.xqy";

declare variable $metric as xs:string external;
declare variable $date_property as xs:string external;
declare variable $buckets as xs:string external;
declare variable $search_parameters as xs:string external;

let $document-query := filters:build-search-query(xdmp:from-json-string($search_parameters))
let $reference := cts:element-reference(fn:QName("", $metric), "type=long")
let $date-name := fn:QName("", $date_property)
let $options := ("properties", "fragment-frequency")
let $result := map:map()
let $_ :=
    for $bucket in json:array-values(xdmp:from-json-string($buckets))
    let $query := cts:and-query((
        cts:document-fragment-query($document-query),
        cts:element-range-query($date-name, ">=", xs:dateTime(map:get($bucket, "start"))),
        cts:element-range-query($date-name, "<", xs:dateTime(map:get($bucket, "end"))),
        (: 1970-01-01 is the unknown-publication-date sentinel. :)
        cts:not-query(cts:element-range-query($date-name, "=", xs:dateTime("1970-01-01T00:00:00Z")))
    ))
    let $count := cts:count-aggregate($reference, $options, $query)
    let $statistics := map:map()
        => map:with("count", $count)
        => map:with("sum", if ($count = 0) then 0 else cts:sum-aggregate($reference, $options, $query))
        => map:with("mean", if ($count = 0) then null-node {} else cts:avg-aggregate($reference, $options, $query))
        => map:with("median", if ($count = 0) then null-node {} else cts:median(cts:values($reference, (), $options, $query)))
    return map:put($result, map:get($bucket, "label"), $statistics)
return xdmp:to-json-string($result)

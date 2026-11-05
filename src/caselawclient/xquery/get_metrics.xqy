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
let $is-duration := $metric = ("tdr_to_first_publish", "tdr_to_latest_publish")
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
    let $over-query := cts:and-query((
        $query,
        cts:element-range-query(fn:QName("", $metric), ">", xs:long(86400))
    ))
    let $over-count := if ($is-duration and $count > 0)
        then cts:count-aggregate($reference, $options, $over-query) else 0
    let $statistics := map:map()
        => map:with("count", $count)
        => map:with("sum", if ($count = 0) then 0 else cts:sum-aggregate($reference, $options, $query))
        => map:with("mean", if ($count = 0) then null-node {} else cts:avg-aggregate($reference, $options, $query))
        => map:with("median", if ($count = 0) then null-node {} else cts:median(cts:values($reference, (), $options, $query)))
        => map:with("within_24_hours_count", if ($is-duration) then $count - $over-count else null-node {})
        => map:with("over_24_hours_count", if ($is-duration) then $over-count else null-node {})
        => map:with("over_24_hours_mean", if ($over-count = 0) then null-node {} else cts:avg-aggregate($reference, $options, $over-query))
        => map:with("minimum", if ($count = 0) then null-node {} else cts:min($reference, $options, $query))
        => map:with("maximum", if ($count = 0) then null-node {} else cts:max($reference, $options, $query))
        => map:with("standard_deviation", if ($count = 0) then null-node {} else cts:stddev-p($reference, $options, $query))
    return map:put($result, map:get($bucket, "label"), $statistics)
return xdmp:to-json-string($result)

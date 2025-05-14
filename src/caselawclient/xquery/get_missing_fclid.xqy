xquery version "1.0-ml";

declare variable $maximum_records as xs:int? external := 1000;

for $doc in fn:subsequence(
  cts:search(
    fn:collection(),
    cts:and-query(
      (
        cts:properties-fragment-query(
          cts:element-value-query(xs:QName("published"), "true")
        ),
        cts:not-query(
          cts:properties-fragment-query(
            cts:element-value-query(xs:QName("namespace"), "fclid")
          )
        )
      )
    )
  ),
  1,
  $maximum_records
)

return fn:base-uri($doc)

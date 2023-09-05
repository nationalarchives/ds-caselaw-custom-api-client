xquery version "1.0-ml";

(: All documents must not have more than one document collection :)

cts:uris(
    (),
    (),
    cts:and-query(
      (cts:collection-query(("judgment")),
      (cts:collection-query(("press-summary"))))
    )
)

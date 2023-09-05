xquery version "1.0-ml";

(: All documents must have at least one document collection (from judgment, press-summary) :)

cts:uris(
    (),
    (),
    cts:not-query(cts:collection-query(("judgment", "press-summary")))
)

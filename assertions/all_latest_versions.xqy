xquery version "1.0-ml";

(: All documents at sensible urls are a part of dls:latest-version :)

for $uri in cts:uris(
    (),
    (),
    cts:not-query(cts:collection-query(("http://marklogic.com/collections/dls/latest-version"))))


return if (fn:contains($uri, '_xml_versions')) then () else $uri

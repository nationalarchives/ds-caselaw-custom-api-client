xquery version "1.0-ml";

declare variable $uri as xs:string external;

return xdmp:parse-dateTime(
         "[Y0001]-[M01]-[D01]T[h01]:[m01]:[s01][Z]",
         xdmp:document-properties($uri)//prop:last-modified/text()
)

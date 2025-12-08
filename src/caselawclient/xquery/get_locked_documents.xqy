xquery version "1.0-ml";

for $lock in xdmp:document-locks()
let $uri := xdmp:node-uri($lock)

return
    <lock>
        <document>{$uri}</document>
        <details>{$lock}</details>
    </lock>

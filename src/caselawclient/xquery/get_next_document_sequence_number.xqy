xquery version "1.0-ml";
declare option xdmp:transaction-mode "update";

let $_ := xdmp:set-transaction-mode("update")
let $state_doc := fn:doc("state.xml")
let $counter_node := $state_doc/state/document_counter

let $current_counter := $counter_node/text()
let $new_counter := fn:sum(($current_counter, 1))

let $_ := xdmp:node-replace($counter_node, <document_counter>{$new_counter}</document_counter>)
let $_ := xdmp:commit()

return $new_counter

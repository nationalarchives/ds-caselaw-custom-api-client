xquery version "1.0-ml";

import module namespace dls = "http://marklogic.com/xdmp/dls"
      at "/MarkLogic/dls.xqy";

declare variable $uri as xs:string external;
declare variable $judgment as xs:string external;
declare variable $annotation as xs:string external;
declare variable $from_version as xs:int? external;

let $judgment_xml := xdmp:unquote($judgment)
let $current_doc := fn:doc($uri)
let $current_version := 
  if ($current_doc) then
    let $versions := dls:document-version-list($uri)
    return
      if ($versions) then
        xs:integer($versions[1]/@version-id)
      else
        0
  else
    0
let $version_mismatch :=
  if ($from_version) then
    $current_version ne $from_version
  else
    fn:false()

return
  if ($version_mismatch) then
    fn:error(
      xs:QName("VERSION-MISMATCH"),
      fn:concat(
        "Document version mismatch. Expected version ",
        xs:string($from_version),
        " but found version ",
        xs:string($current_version)
      )
    )
  else
    dls:document-checkout-update-checkin(
      $uri,
      $judgment_xml,
      $annotation,
      fn:true()
    )
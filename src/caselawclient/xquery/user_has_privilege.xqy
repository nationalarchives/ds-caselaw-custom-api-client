xquery version "1.0-ml";

declare variable $privilege_uri as xs:string external;
declare variable $privilege_action as xs:string external;
declare variable $user as xs:string external;

let $privilege_id := xdmp:privilege($privilege_uri, $privilege_action)
let $user_privileges := xdmp:user-privileges($user)

return fn:boolean(index-of($privilege_id, $user_privileges))

xquery version "1.0-ml";

declare variable $user as xs:string external;
declare variable $role as xs:string external;

let $user_roles := xdmp:user-roles($user)
let $role_id := xdmp:role($role)

return fn:boolean(index-of($role_id, $user_roles))

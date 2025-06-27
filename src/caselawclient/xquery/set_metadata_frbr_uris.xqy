xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare variable $uri as xs:string external;
declare variable $work as xs:string external;
declare variable $expression as xs:string external;
declare variable $manifestation as xs:string external;

(
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRuri,
    <akn:FRBRuri value="{$work}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    ),
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRthis,
    <akn:FRBRthis value="{$work}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    ),
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRExpression/akn:FRBRuri,
    <akn:FRBRuri value="{$expression}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    ),
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRExpression/akn:FRBRthis,
    <akn:FRBRthis value="{$expression}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    ),
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRManifestation/akn:FRBRuri,
    <akn:FRBRuri value="{$manifestation}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    ),
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRManifestation/akn:FRBRthis,
    <akn:FRBRthis value="{$manifestation}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    )
)

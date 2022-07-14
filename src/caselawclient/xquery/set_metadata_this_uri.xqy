xquery version "1.0-ml";

declare namespace akn = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0";
declare variable $uri as xs:string external;
declare variable $content_with_id as xs:string external;
declare variable $content_without_id as xs:string external;
declare variable $content_with_xml as xs:string external;

(
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRuri,
    <akn:FRBRuri value="{$content_with_id}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    ),
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRthis,
    <akn:FRBRthis value="{$content_with_id}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    ),
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRExpression/akn:FRBRuri,
    <akn:FRBRuri value="{$content_without_id}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    ),
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRExpression/akn:FRBRthis,
    <akn:FRBRthis value="{$content_without_id}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    ),
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRManifestation/akn:FRBRuri,
    <akn:FRBRuri value="{$content_with_xml}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    ),
  xdmp:node-replace(
    document($uri)/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRManifestation/akn:FRBRthis,
    <akn:FRBRthis value="{$content_with_xml}" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>
    )
)

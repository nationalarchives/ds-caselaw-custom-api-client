declare namespace uk="https://caselaw.nationalarchives.gov.uk/akn";
declare variable $uri as xs:string external;
declare variable $decision_date as xs:string external;
declare variable $transform_datetime as xs:string external;
declare variable $court_code as xs:string external;
declare variable $title as xs:string external;
declare variable $year as xs:string external;
declare variable $court_url as xs:string external;
declare variable $court_full_name as xs:string external;
declare variable $case_numbers as array(xs:string) external;
declare variable $parties as array(map(xs:string, xs:string)) external;

let $court_code_lower := fn:lower-case($court_code)
let $court_code_upper := fn:upper-case($court_code)

let $case_numbers_xml := array:for-each($case_numbers, function($case) {
  <uk:caseNumber>{$case}</uk:caseNumber>
})

let $parties_xml := array:for-each($parties, function($party) {
  <uk:party role="{$party("role")}">{$party("name")}</uk:party>
})

return
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
  <judgment name="decision">
    <meta>
      <identification source="#tna">
        <FRBRWork>
          <FRBRthis value="" />
          <FRBRuri value="" />
          <FRBRdate date="{$decision_date}" name="decision" />
          <FRBRauthor href="#{$court_code_lower}" />
          <FRBRcountry value="GB-UKM" />
          <FRBRname value="{$title}" />
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="" />
          <FRBRuri value="" />
          <FRBRdate date="{$decision_date}" name="decision" />
          <FRBRauthor href="#{$court_code_lower}" />
          <FRBRlanguage language="eng" />
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="" />
          <FRBRuri value="" />
          <FRBRdate date="{$transform_datetime}" name="transform" />
          <FRBRauthor href="#tna" />
          <FRBRformat value="application/xml" />
        </FRBRManifestation>
      </identification>
      <lifecycle source="#">
        <eventRef date="{$decision_date}" refersTo="#decision" source="#" />
      </lifecycle>
      <references source="#tna">
        <TLCOrganization
          eId="tna"
          href="https://www.nationalarchives.gov.uk/"
          showAs="The National Archives"
          />
        <TLCOrganization
          eId="{$court_code_lower}"
          href="{$court_url}"
          showAs="{$court_full_name}"
          />
        <TLCEvent eId="decision" href="#" showAs="decision" />
      </references>
      <proprietary
        xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
        source="#"
        >
        <uk:court>{$court_code_upper}</uk:court>
        <uk:year>{$year}</uk:year>
        {$case_numbers_xml}
        {$parties_xml}
        <uk:sourceFormat>application/pdf</uk:sourceFormat>
      </proprietary>
    </meta>
    <header />
    <judgmentBody>
      <decision>
        <p />
      </decision>
    </judgmentBody>
  </judgment>
</akomaNtoso>

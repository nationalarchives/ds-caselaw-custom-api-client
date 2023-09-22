xquery version "1.0-ml";
import module namespace dls = "http://marklogic.com/xdmp/dls" at "/MarkLogic/dls.xqy";
let $URI := "/smoketest/1001/2.xml"
let $doc := <akomaNtoso
  xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
  xmlns:html="http://www.w3.org/1999/xhtml"
  xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
  <judgment name="judgment">
    <meta>
      <identification source="#tna">
        <FRBRWork>
        <FRBRdate date="1001-02-03" name="judgment"/>
        <FRBRname value="cats v dogs"/>
       </FRBRWork>
       <FRBRExpression>
         <FRBRdate date="1001-02-03" name="judgment"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRdate date="2023-03-16T00:00:00" name="transform"/>
        </FRBRManifestation>
      </identification>
      <references source="#tna"/>
        <proprietary source="#">

          <uk:court>EWHC-Chancellery</uk:court>
          <uk:year>2023</uk:year>
          <uk:number>1234</uk:number>
          <uk:cite>[2023] EAT 1234</uk:cite>
          <uk:parser>0.13.3</uk:parser>
          <uk:hash>1234</uk:hash>
        </proprietary>
    </meta>
  </judgment>
</akomaNtoso>

return dls:document-insert-and-manage($URI, fn:false(), $doc, "this is an annotation", (), ("judgment") )

xquery version "1.0-ml";
import module namespace dls = "http://marklogic.com/xdmp/dls"
   at "/MarkLogic/dls.xqy";
dls:validate-all-documents(  fn:true() )

xquery version "1.0-ml"; 
 
import module namespace admin = "http://marklogic.com/xdmp/admin" at "/MarkLogic/admin.xqy";

declare variable $CLUSTER-NAME := xdmp:get-request-field("CLUSTER-NAME",xdmp:host-name(xdmp:host())) ;

xdmp:set-response-content-type("text/html"),
let $null := admin:save-configuration(admin:cluster-set-name(admin:get-configuration(), $CLUSTER-NAME))
return
fn:concat("Cluster name set to ",$CLUSTER-NAME)
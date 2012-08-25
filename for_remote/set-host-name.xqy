xquery version "1.0-ml";

import module namespace admin = "http://marklogic.com/xdmp/admin" at "/MarkLogic/admin.xqy";

declare variable $HOST-NAME := xdmp:get-request-field("HOST-NAME",xdmp:host-name(xdmp:host()));
		
let $config := admin:get-configuration()
let $hostid := xdmp:host()
return
admin:save-configuration(admin:host-set-name($config, $hostid, $HOST-NAME))
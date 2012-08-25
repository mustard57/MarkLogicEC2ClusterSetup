xquery version "0.9-ml"

(: add hosts to Cluster :)

default element namespace = "http://www.w3.org/1999/xhtml"
declare namespace xs="http://www.w3.org/2001/XMLSchema"
declare namespace gr="http://marklogic.com/xdmp/group"
declare namespace db="http://marklogic.com/xdmp/database"
declare namespace err="http://marklogic.com/xdmp/error"
declare namespace ho="http://marklogic.com/xdmp/hosts"
declare namespace as="http://marklogic.com/xdmp/assignments"
declare namespace mi="http://marklogic.com/xdmp/mimetypes"
declare namespace sec="http://marklogic.com/xdmp/security"

let 	$server := xdmp:get-request-field("server"),
    	$joiner := xdmp:get-request-field("joiner"),
(: 	$joiner := if($joiner eq xdmp:hostname()) then $joiner else
		   substring-before($joiner,"."),
        $server := if($joiner eq xdmp:hostname()) then $server else
                   substring-before($server,"."), :)
	$user := xdmp:get-request-field("user","admin"),
	$pass := xdmp:get-request-field("pass","admin"),
	$port := xdmp:get-request-field("port", "8001"),
	$bind := xdmp:get-request-field("bind","7999"),
	$foreign-bind := xdmp:get-request-field("foreign-bind","7998"),	
	$foreign-connect := xdmp:get-request-field("foreign-connect","7998"),	
	$connect := xdmp:get-request-field("connect","7999"), 
	$protocol := xdmp:get-request-field("protocol", "http"),
	$ssl-certificate := xdmp:base64-encode(xdmp:read-cluster-config-file("hosts.xml")//ho:host[contains(ho:host-name,$joiner)]/ho:ssl-certificate),
	$host-id := xdmp:read-cluster-config-file("hosts.xml")//ho:host[contains(ho:host-name,$joiner)]/ho:host-id/text(),
	$get-grp-info := xdmp:http-get( concat($protocol,"://",$server,":",$port,"/accept-joiner.xqy?joiner=",$joiner,"&port=",$port,"&bind=",$bind,"&foreign-bind=",$foreign-bind,"&foreign-connect=",$foreign-connect, "&connect=",$connect, "&protocol=", $protocol, "&ssl-certificate=", $ssl-certificate, "&host-id=", $host-id, "&joiner-host-id=", $host-id, "&server=", $server),
                <options xmlns="xdmp:http">
        	<authentication method="digest">
         		<username>{$user}</username>
         		<password>{$pass}</password>
       		</authentication>
		<format xmlns="xdmp:document-get">xml</format>
     		</options>),
	$group := fn:data(($get-grp-info[2])//*:select[@name="group"]/option/@value),
	$addHost := xdmp:http-get( concat($protocol,"://",$server,":",$port,"/accept-joiner-go.xqy?joiner=",$joiner,"&port=",$port,"&bind=",$bind,"&foreign-bind=",$foreign-bind,"&foreign-connect=",$foreign-connect, "&connect=",$connect, "&protocol=", $protocol, "&ssl-certificate=", $ssl-certificate, "&host-id=", $host-id, "&joiner-host-id=", $host-id, "&server=", $server, "&group=", $group),
                <options xmlns="xdmp:http">
        	<authentication method="digest">
         		<username>{$user}</username>
         		<password>{$pass}</password>
       		</authentication>
		<format xmlns="xdmp:document-get">xml</format>
     		</options>)

return ($addHost)

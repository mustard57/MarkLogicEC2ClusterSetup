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
declare namespace cl="http://marklogic.com/xdmp/clusters"


let 	$server := xdmp:get-request-field("server"),
    	$joiner := xdmp:get-request-field("joiner"),
	$user := xdmp:get-request-field("user","admin"),
	$pass := xdmp:get-request-field("pass","admin"),
	$port := xdmp:get-request-field("port", "8001"),
	$bind := xdmp:get-request-field("bind","7999"),
	$connect := xdmp:get-request-field("connect","7999"), 
	$protocol := xdmp:get-request-field("protocol", "http"),
	$assignmentsFile := xdmp:url-encode(xdmp:quote(xdmp:read-cluster-config-file("assignments.xml")/as:assignments)),
	$clustersFile := xdmp:url-encode(xdmp:base64-encode(xdmp:quote(xdmp:read-cluster-config-file("clusters.xml")/cl:clusters))),

 	$databasesFile := xdmp:url-encode(xdmp:quote(xdmp:read-cluster-config-file("databases.xml")/db:databases)),
	$groupsFile := xdmp:url-encode(xdmp:quote(xdmp:read-cluster-config-file("groups.xml")/gr:groups)),
	$hostsFile := xdmp:url-encode(xdmp:base64-encode(xdmp:quote(xdmp:read-cluster-config-file("hosts.xml")/ho:hosts))),
	$mimetypesFile := xdmp:url-encode(xdmp:quote(xdmp:read-cluster-config-file("mimetypes.xml")/mi:mimetypes)),
	$copyConfigFiles := xdmp:http-post( concat( $protocol, "://",$joiner,":",$port,"/receive-config-go.xqy"),
		<options xmlns="xdmp:http">
		<headers>
			<content-type>application/x-www-form-urlencoded</content-type>
		</headers>
		<authentication method="digest">
         		<username>{$user}</username>
         		<password>{$pass}</password>
       		</authentication>
		<data> { concat( "assignmentsFile=", $assignmentsFile, "&clustersFile=", $clustersFile,"&databasesFile=", $databasesFile, "&groupsFile=", $groupsFile, "&hostsFile=", $hostsFile, "&mimetypesFile=", $mimetypesFile, "&protocol=", $protocol )
		}
		</data>
     		</options>)
(:
return ($assignmentsFile,$databasesFile,$groupsFile, $hostsFile, $mimetypesFile)
:)
return ($copyConfigFiles)

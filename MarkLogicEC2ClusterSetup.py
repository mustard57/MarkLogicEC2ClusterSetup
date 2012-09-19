import MarkLogicEC2Lib
import sys

THAW_MODE = "thaw"
HELP_MODE = "help"
FREEZE_MODE  = "freeze"
STATUS_MODE = "status"
CLUSTER_MODE = "cluster"
CLEAN_MODE = "clean"

MODES = (THAW_MODE,HELP_MODE,FREEZE_MODE,CLUSTER_MODE,CLEAN_MODE)

# Get mode
if(len(sys.argv) > 1):
	mode = sys.argv[1]
else:
	mode = ""

print "Run mode is "+mode

if(mode == THAW_MODE):
	if(len(sys.argv) > 2):
		host = MarkLogicEC2Lib.getHostForRequest(sys.argv[2])
		MarkLogicEC2Lib.startInstance(host)
	else:
		for host in MarkLogicEC2Lib.getAvailableHosts():
			MarkLogicEC2Lib.startInstance(host)
elif(mode == FREEZE_MODE):
	if(len(sys.argv) > 2):
		host = MarkLogicEC2Lib.getHostForRequest(sys.argv[2])
		MarkLogicEC2Lib.stopInstance(host)
	else:
		for host in MarkLogicEC2Lib.getAvailableHosts():
			MarkLogicEC2Lib.stopInstance(host)
elif(mode == STATUS_MODE):
	if(len(sys.argv) > 2):
		host = MarkLogicEC2Lib.getHostForRequest(sys.argv[2])
		print "host "+host+ "is in the " + MarkLogicEC2Lib.getInstanceStatus(host) + " state"
	else:
		for host in MarkLogicEC2Lib.getAvailableHosts():
			print "Host "+host+ "is in the " + MarkLogicEC2Lib.getInstanceStatus(host) + " state"
elif(mode == HELP_MODE):		
	print "Available modes are "+",".join(MODES)
elif(mode == CLUSTER_MODE):
	ROOT_HOST = ""

	for host in MarkLogicEC2Lib.getAvailableHosts():
		MarkLogicEC2Lib.nameHost(host)		
		MarkLogicEC2Lib.httpProcess("Restarting...","http://" + MarkLogicEC2Lib.getInstance(host).public_dns_name + ":8001/restart.xqy")
	
	for host in MarkLogicEC2Lib.getAvailableHosts():
		MarkLogicEC2Lib.configureAuthHttpProcess(MarkLogicEC2Lib.getInstance(host).public_dns_name)	
		if ROOT_HOST:
			args = {'server' : ROOT_HOST, 'joiner' : MarkLogicEC2Lib.getInstance(host).public_dns_name }
			MarkLogicEC2Lib.httpProcess("Joining Cluster","http://" + MarkLogicEC2Lib.getInstance(host).public_dns_name + ":8001/join-cluster.xqy", args)
		else:
			ROOT_HOST = MarkLogicEC2Lib.getInstance(host).public_dns_name

	ROOT_HOST = ""

	for host in MarkLogicEC2Lib.getAvailableHosts():
		if ROOT_HOST:
			args = {'server' : ROOT_HOST, 'joiner' : MarkLogicEC2Lib.getInstance(host).public_dns_name }
			MarkLogicEC2Lib.configureAuthHttpProcess(ROOT_HOST)
			MarkLogicEC2Lib.httpProcess("Joining Cluster II","http://" + ROOT_HOST + ":8001/transfer-cluster-config.xqy",args)
			MarkLogicEC2Lib.configureAuthHttpProcess(MarkLogicEC2Lib.getInstance(host).public_dns_name)
			MarkLogicEC2Lib.httpProcess("Restarting...","http://" + MarkLogicEC2Lib.getInstance(host).public_dns_name + ":8001/restart.xqy")
		else:
			ROOT_HOST = MarkLogicEC2Lib.getInstance(host).public_dns_name

	MarkLogicEC2Lib.configureAuthHttpProcess(ROOT_HOST)
	MarkLogicEC2Lib.httpProcess("Cluster name","http://" + ROOT_HOST + ":8001/set-cluster-name.xqy",{"CLUSTER-NAME":CLUSTER_NAME})	
elif(mode == CLEAN_MODE):
	MarkLogicEC2Lib.clean()
else:
	print mode +" is not a permitted mode"
		
	

# Tasks
# Host Create
# Host setup
# Freeze
# Thaw

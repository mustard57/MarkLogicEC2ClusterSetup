from MarkLogicEC2Config import HOST_FILE,CLUSTER_NAME
from MarkLogicEC2Lib import sys,configureAuthHttpProcess,httpProcess

import boto

def get_instance(instance_id):
	instance=None
	for i in ec2.get_all_instances():
		if i.instances[0].id == instance_id:
			instance = i.instances[0]
	return instance

# EC2 connection 
ec2 = boto.connect_ec2()

f = open(HOST_FILE)

ROOT_HOST = ""
for line in f.xreadlines():
	host =  line.strip()
	dns_name  = get_instance(host).public_dns_name
	configureAuthHttpProcess(dns_name)

	if ROOT_HOST:
		args = {'server' : ROOT_HOST, 'joiner' : dns_name }
		httpProcess("Joining Cluster","http://" + dns_name + ":8001/join-cluster.xqy", args)
	else:
		ROOT_HOST = dns_name

f.close()		
		
f = open(HOST_FILE)
		
ROOT_HOST = ""

for line in f.xreadlines():
	host =  line.strip()
	dns_name  = get_instance(host).public_dns_name

	if ROOT_HOST:
		args = {'server' : ROOT_HOST, 'joiner' : dns_name }
		configureAuthHttpProcess(ROOT_HOST)
		httpProcess("Joining Cluster II","http://" + ROOT_HOST + ":8001/transfer-cluster-config.xqy",args)
		configureAuthHttpProcess(dns_name)
		httpProcess("Restarting...","http://" + dns_name + ":8001/restart.xqy")
	else:
		ROOT_HOST = dns_name

configureAuthHttpProcess(ROOT_HOST)
httpProcess("Cluster name","http://" + ROOT_HOST + ":8001/set-cluster-name.xqy",{"CLUSTER-NAME":CLUSTER_NAME})
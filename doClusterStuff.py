import os
import sys
import ConfigParser
import boto

import urllib
import urllib2

def get_instance(instance_id):
	instance=None
	for i in ec2.get_all_instances():
		if i.instances[0].id == instance_id:
			instance = i.instances[0]
	return instance

def sys(message, cmd):
	print(message)
	os.system(cmd)
	time.sleep(10)
	
def httpProcess(message, url, args = "", debug = False):
	print message
	request = urllib2.Request(url)
	if args == "":
		response = urllib2.urlopen(request)
	else:
		response = urllib2.urlopen(request, urllib.urlencode(args))
	if (debug == True):
		data = response.read()
		print data
		
def configureAuthHttpProcess(host):
	href = "http://"+host+":8001"
	passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
	passman.add_password(None, href, ADMIN_USER_NAME, ADMIN_PASSWORD)
	authhandler = urllib2.HTTPDigestAuthHandler(passman)
	opener = urllib2.build_opener(authhandler)
	urllib2.install_opener(opener)		


# EC2 connection 
ec2 = boto.connect_ec2()

# Configuration
CONFIG_FILE="config.ini"
                                     									 
parser = ConfigParser.ConfigParser()
parser.read(CONFIG_FILE)

HOST_FILE = parser.get("Constants","HOST_FILE")
ADMIN_USER_NAME=parser.get("Configuration","ADMIN_USER_NAME")
ADMIN_PASSWORD=parser.get("Configuration","ADMIN_PASSWORD")
CLUSTER_NAME=parser.get("Configuration","CLUSTER_NAME")

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
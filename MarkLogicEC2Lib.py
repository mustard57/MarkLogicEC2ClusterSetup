import os
import sys
import time
import urllib
import urllib2
import boto
import re
import rsa	
import glob
import MarkLogicEC2Config

# Constants
SLEEP_PERIOD = 30
EC2_RESOLUTION_URL = "http://169.254.169.254/2009-04-04/meta-data/public-hostname"

ec2 = boto.connect_ec2()

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
	print "Configuring auth for " + href
	passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
	passman.add_password(None, href, MarkLogicEC2Config.ADMIN_USER_NAME, MarkLogicEC2Config.ADMIN_PASSWORD)
	authhandler = urllib2.HTTPDigestAuthHandler(passman)
	opener = urllib2.build_opener(authhandler)
	urllib2.install_opener(opener)		

def getEC2Name():
	request = urllib2.Request(EC2_RESOLUTION_URL)
	response = urllib2.urlopen(request)	
	data = response.read().decode()	
	return data

def clearDirectory(dirName):
	if os.path.isdir(dirName):
		for file in os.listdir(dirName):
			os.remove(dirName + "/" + file)

def removeDirectory(dirName):
	if os.path.isdir(dirName):
		os.rmdir(dirName)
			
def checkDirectory(dirName):
	if not os.path.isdir(dirName):
		os.makedirs(dirName)

def checkDirectories():
	checkDirectory(MarkLogicEC2Config.POWERSHELL_DIR)
	checkDirectory(MarkLogicEC2Config.HTML_DIR)
	checkDirectory(MarkLogicEC2Config.MSTSC_DIR)
	checkDirectory(MarkLogicEC2Config.SESSION_DIR)

def clearDirectories():
	clearDirectory(MarkLogicEC2Config.POWERSHELL_DIR)
	clearDirectory(MarkLogicEC2Config.HTML_DIR)
	clearDirectory(MarkLogicEC2Config.MSTSC_DIR)
	clearDirectory(MarkLogicEC2Config.SESSION_DIR)

def removeDirectories():
	removeDirectory(MarkLogicEC2Config.POWERSHELL_DIR)
	removeDirectory(MarkLogicEC2Config.HTML_DIR)
	removeDirectory(MarkLogicEC2Config.MSTSC_DIR)
	removeDirectory(MarkLogicEC2Config.SESSION_DIR)

def getHostForRequest(input):
	host = ""
	hosts = getAvailableHosts()
	if(re.compile('^\d+$').match(input)):
		if(int(input) <= len(hosts)):
			host = hosts[int(input) - 1]
		else:
			print "The host number you requested does not exist. Please choose from " + str(len(hosts)) + " or below"
			exit()
	else:
		if(input in hosts):
			host = input
		else:
			print "The host "+input+" does not exist"
			exit()
	return host

def getAvailableHosts():			
	f = open(MarkLogicEC2Config.HOST_FILE)
	hosts = []
	for line in f.xreadlines():
		hosts.append(line.strip())
	return hosts
	
def startInstance(host):
	if(not(isRunning(host))):
		print "Starting host "+host
		ec2.start_instances(host)
		waitForRunningState(host)
		createRDPLink(host)
		createAdminConsoleLink(host)
		createSessionLink(host)
		# nameHost(host)
		print "Host started"				
	else:
		print "Host " + host + " already running"
		
def stopInstance(host):
	if(not(isStopped(host))):
		print "Stopping host "+host
		ec2.stop_instances(host)
		removeRDPLink(host)
		removeAdminConsoleLink(host)
		removeSessionLink(host)
		waitForStoppedState(host)		
		print "Host stopped"				
	else:
		print "Host " + host + " already stopped"

def getInstance(host):
	return ec2.get_all_instances(host)[0].instances[0]

def getInstanceStatus(host):
	return getInstance(host).state

def isRunning(host):
	return getInstance(host).state == 'running'

def isStopped(host):
	return getInstance(host).state == 'stopped'

def adminURL(host_name):
	return "http://"+host_name+":8001/"
	
def nameHost(host):	
	dns_name = getInstance(host).public_dns_name
	HOST_ARGS = { 'HOST-NAME':dns_name }
	configureAuthHttpProcess(dns_name)
	httpProcess("Setting host name",adminURL(dns_name) +"set-host-name.xqy", HOST_ARGS)

def getPassword(host):
	password = ""
	if(MarkLogicEC2Config.MSTSC_PASSWORD):
		password = MarkLogicEC2Config.MSTSC_PASSWORD
	else:
		password = getDefaultPassword(host)
	return password

def getDefaultPassword(host):	
	instance = getInstance(host)
	while True:		
		dns_name =  instance.public_dns_name
		instance_id =  instance.id

		# Get Encrypted password
		encrypted_pword = ec2.get_password_data(instance.id).strip("\n\r\t").decode('base64')

		with open(MarkLogicEC2Config.RSA_PRIVATE_KEY) as privatefile:
			keydata = privatefile.read()
		privkey = rsa.PrivateKey.load_pkcs1(keydata)

		# Get decrypted password
		if encrypted_pword:
			password = rsa.decrypt(encrypted_pword,privkey)		
			break
		else:
			print "No password available yet - sleeping for "+str(SLEEP_PERIOD) + " secs"
			time.sleep(SLEEP_PERIOD)
	return password
	
	
def createAdminConsoleLink(host):
	dns_name = getInstance(host).public_dns_name	
	f = open(MarkLogicEC2Config.HTML_DIR + "\\" + dns_name + ".admin.html","w")
	f.write("<html><head><script>window.location = 'http://" + dns_name +":8001';</script></head><body></body></html>")
	f.close()

def removeAdminConsoleLink(host):
	dns_name = getInstance(host).public_dns_name	
	if os.path.isfile(MarkLogicEC2Config.HTML_DIR + "\\" + dns_name + ".admin.html"):	
		os.remove(MarkLogicEC2Config.HTML_DIR + "\\" + dns_name + ".admin.html")
	
def createRDPLink(host):
	dns_name = getInstance(host).public_dns_name	
	f = open(MarkLogicEC2Config.MSTSC_DIR + "\\" + dns_name + ".rdp","w")
	f.write("auto connect:i:1\n")
	f.write("full address:s:"+dns_name+"\n")
	f.write("username:s:Administrator\n")
	f.close()

def removeRDPLink(host):
	dns_name = getInstance(host).public_dns_name	
	if os.path.isfile(MarkLogicEC2Config.MSTSC_DIR + "\\" + dns_name + ".rdp"):
		os.remove(MarkLogicEC2Config.MSTSC_DIR + "\\" + dns_name + ".rdp")
	
def createSessionLink(host):	
	dns_name = getInstance(host).public_dns_name	
	password = getPassword(host)
	instance_id = getInstance(host).id
	f = open(MarkLogicEC2Config.SESSION_DIR  +"\\"+dns_name+".session.ps1","w")
	f.write('Set-ItemProperty -Path HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -Name LocalAccountTokenFilterPolicy -Value 1 -Type DWord\n')
	f.write('Set-Item WSMan:\\localhost\\Client\TrustedHosts -Value ' + dns_name + " -Force -Concatenate\n")
	f.write("$pw = convertto-securestring -AsPlainText -Force -String '"+password+"'\n")
	f.write('$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist "'+instance_id+'\Administrator",$pw\n')
	f.write('$session = new-pssession -computername '+dns_name + ' -credential $cred\n')
	f.write('Enter-PSSession $session\n')
	f.close()
	
def removeSessionLink(host):
	dns_name = getInstance(host).public_dns_name	
	if os.path.isfile(MarkLogicEC2Config.SESSION_DIR + "\\" + dns_name + ".session.ps1"):
		os.remove(MarkLogicEC2Config.SESSION_DIR + "\\" + dns_name + ".session.ps1")

def waitForRunningState(host):	
	while True:		
		instance = getInstance(host)
		if isRunning(host):
			break
		else:
			print "Instance not yet in running state"
		time.sleep(SLEEP_PERIOD)

def waitForStoppedState(host):	
	while True:		
		instance = getInstance(host)
		if isStopped(host):
			break
		else:
			print "Instance not yet in stopped state"
		time.sleep(SLEEP_PERIOD)

def clean():
	if os.path.isfile(MarkLogicEC2Config.HOST_FILE):
		for host in getAvailableHosts():		
			getInstance(host).terminate()
			
	for address in ec2.get_all_addresses():
		address.release()

	clearDirectories()	
	removeDirectories()

	if os.path.isfile(MarkLogicEC2Config.HOST_FILE):
		os.remove(MarkLogicEC2Config.HOST_FILE)
	for file in glob.glob("*.pyc"):
		os.remove(file)
			
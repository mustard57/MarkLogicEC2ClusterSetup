import MarkLogicEC2Lib
import MarkLogicEC2Config
import sys
import boto
import time
import os
import glob
import rsa

SLEEP_PERIOD = 30
ec2 = boto.connect_ec2()

def getAvailableHosts():			
	f = open(MarkLogicEC2Config.HOST_FILE)
	hosts = []
	for line in f.xreadlines():
		hosts.append(line.strip())
	return hosts

def isRootHost(host):
	return os.path.isfile(MarkLogicEC2Config.HOST_FILE) and (len(getAvailableHosts()) > 0) and (getAvailableHosts()[0] == host)

def getRootIP():
	ip = ""
	if os.path.isfile(MarkLogicEC2Config.ROOT_IP_FILE):
		f = open(MarkLogicEC2Config.ROOT_IP_FILE)
		ip = f.readline()
		f.close()
	return str(ip)

def getRootElasticIP():
	for address in ec2.get_all_addresses():
		if str(address) == getRootIP():
			break
	return address				
	
def startInstance(host):
	if(not(isRunning(host))):
		print "Starting host "+host
		ec2.start_instances(host)
		waitForRunningState(host)
		if(isRootHost(host) and getRootIP()):
			getRootElasticIP().associate(host)
			print "Elastic IP added for root host " + host + " - " + getRootIP()
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

def createHost():
	cmd = '<powershell>Enable-PSRemoting -Force</powershell>'	
	reservation = ec2.run_instances(image_id='ami-71b50018',instance_type="t1.micro",key_name="HP",security_groups=["MarkLogic"],user_data=cmd)
	instance = ec2.get_all_instances()[-1].instances[0]
	print "Created instance "+ instance.id
	
	waitForRunningState(str(instance.id))

	f = open(MarkLogicEC2Config.HOST_FILE,"a")
	f.write(instance.id+"\n")
	f.close()	
	
	if isRootHost(instance.id):
		allocateIP(instance.id)
	

def allocateIP(host):
	if(len(ec2.get_all_addresses()) >= MarkLogicEC2Config.EC2_ELASTIC_IP_LIMIT):
		print "You've used "+str(MarkLogicEC2Config.EC2_ELASTIC_IP_LIMIT)+" elastic IP addresses which is the limit. Configuring without elastic IP"
	else:
		ip = ec2.allocate_address() 	
		ec2.associate_address(instance_id=host,public_ip=ip.public_ip)
		print "Elastic IP "+ip.public_ip+" added"
		f = open(MarkLogicEC2Config.ROOT_IP_FILE,"w")
		f.write(ip.public_ip+"\n")
		f.close()	
	

def setupHost(host):
	instance = getInstance(host)

	dns_name =  instance.public_dns_name

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

	createPythonDownloadScript()
	createMarkLogicDownloadScript()
	
	# Create server setup script
	f = open(MarkLogicEC2Config.POWERSHELL_DIR  +"\\server-setup.ps1","w")
	f.write('Set-ItemProperty -Path HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -Name LocalAccountTokenFilterPolicy -Value 1 -Type DWord\n')
	f.write('Set-Item WSMan:\\localhost\\Client\TrustedHosts -Value ' + dns_name + " -Force\n")
	f.write("$pw = convertto-securestring -AsPlainText -Force -String '"+password+"'\n")
	f.write('$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist "'+instance_id+'\Administrator",$pw\n')
	f.write('$session = new-pssession -computername '+dns_name + ' -credential $cred\n')
	f.write("net use \\\\"+dns_name+" '" + password + "' /user:Administrator\n")
	f.write("copy-item -force -path for_remote\* -destination \\\\"+dns_name+"\\"+MarkLogicEC2Config.INSTALL_DIR.replace(":","$")+"\n")
	f.write("copy-item -force -path config.ini -destination \\\\"+dns_name+"\\"+MarkLogicEC2Config.INSTALL_DIR.replace(":","$")+"\n")
	f.write("copy-item -force -path MarkLogicEC2Config.py -destination \\\\"+dns_name+"\\"+MarkLogicEC2Config.INSTALL_DIR.replace(":","$")+"\n")
	f.write("copy-item -force -path MarkLogicEC2Lib.py -destination \\\\"+dns_name+"\\"+MarkLogicEC2Config.INSTALL_DIR.replace(":","$")+"\n")
	f.write("invoke-command -session $session -filepath pws\downloadpython.ps1\n")	
	f.write("invoke-command -session $session -filepath pws\downloadmarklogic.ps1\n")	
	f.write("sleep 30\n")
	f.write("echo 'installing python'\n")
	f.write("invoke-command -session $session {"+ MarkLogicEC2Config.INSTALL_DIR + MarkLogicEC2Config.PYTHON_EXE+" /passive /quiet}\n")	
	f.write("sleep 60\n")
	f.write("echo 'setting up MarkLogic'\n")
	f.write("invoke-command -session $session {cd " + MarkLogicEC2Config.INSTALL_DIR + " ; " + MarkLogicEC2Config.PYTHON_INSTALL_DIR + "\\python MarkLogicSetup.py}\n")
	f.write("invoke-command -session $session {Set-Service MarkLogic -startuptype 'Automatic'}\n")
	f.write("invoke-command -session $session {netsh firewall set opmode disable}\n")
	if(MarkLogicEC2Config.MSTSC_PASSWORD):
		f.write('invoke-command -session $session {$account = [ADSI]("WinNT://$env:COMPUTERNAME/Administrator,user") ; $account.psbase.invoke("setpassword","'+MarkLogicEC2Config.MSTSC_PASSWORD+'") }\n')
		print "Setting mstsc password as requested"
	else:
		print "MSTSC password set not requested - will use password set by EC2"
	f.close()

	print dns_name
	createRDPLink(host)
	createAdminConsoleLink(host)
	createSessionScript(dns_name,password,instance_id)
	
	print "Finishing "+dns_name+" config at "+time.strftime("%H:%M:%S", time.gmtime())

def createMarkLogicDownloadScript():
	checkDirectory(MarkLogicEC2Config.POWERSHELL_DIR)
	fileName = MarkLogicEC2Config.POWERSHELL_DIR +"\\downloadmarklogic.ps1"
	if not(os.path.isfile(fileName)):
		f = open(fileName,"w")
		f.write('$clnt = new-object System.Net.WebClient\n')
		f.write('$url = "'+MarkLogicEC2Config.MARKLOGIC_DOWNLOAD_URL + MarkLogicEC2Config.MARKLOGIC_EXE+'"\n')
		f.write('$file = "'+MarkLogicEC2Config.INSTALL_DIR + MarkLogicEC2Config.MARKLOGIC_EXE+'"\n')
		f.write('$file\n')
		f.write('$clnt.DownloadFile($url,$file)\n')
		f.close()

def	createAdminConsoleLink(dns_name):
	f = open(MarkLogicEC2Config.HTML_DIR + "\\" + dns_name + ".admin.html","w")
	f.write("<html><head><script>window.location = 'http://" + dns_name +":8001';</script></head><body></body></html>")
	f.close()

def	createRDPLink(dns_name):
	checkDirectory(MarkLogicEC2Config.MSTSC_DIR)	
	f = open(MarkLogicEC2Config.MSTSC_DIR + "\\" + dns_name + ".rdp","w")
	f.write("auto connect:i:1\n")
	f.write("full address:s:"+dns_name+"\n")
	f.write("username:s:Administrator\n")
	f.close()

def createSessionScript(dns_name,password,instance_id):
	checkDirectory(MarkLogicEC2Config.SESSION_DIR)	
	f = open(MarkLogicEC2Config.SESSION_DIR  +"\\"+dns_name+".session.ps1","w")
	f.write('Set-ItemProperty -Path HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -Name LocalAccountTokenFilterPolicy -Value 1 -Type DWord\n')
	f.write('Set-Item WSMan:\\localhost\\Client\TrustedHosts -Value ' + dns_name + " -Force -Concatenate\n")
	f.write("$pw = convertto-securestring -AsPlainText -Force -String '"+password+"'\n")
	f.write('$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist "'+instance_id+'\Administrator",$pw\n')
	f.write('$session = new-pssession -computername '+dns_name + ' -credential $cred\n')
	f.write('Enter-PSSession $session\n')
	f.close()
	
def createAdminConsoleLink(host):
	dns_name = getInstance(host).public_dns_name	
	checkDirectory(MarkLogicEC2Config.HTML_DIR)	
	f = open(MarkLogicEC2Config.HTML_DIR + "\\" + dns_name + ".admin.html","w")
	f.write("<html><head><script>window.location = 'http://" + dns_name +":8001';</script></head><body></body></html>")
	f.close()

def removeAdminConsoleLink(host):
	dns_name = getInstance(host).public_dns_name	
	if os.path.isfile(MarkLogicEC2Config.HTML_DIR + "\\" + dns_name + ".admin.html"):	
		os.remove(MarkLogicEC2Config.HTML_DIR + "\\" + dns_name + ".admin.html")
	
def createRDPLink(host):
	dns_name = getInstance(host).public_dns_name	
	checkDirectory(MarkLogicEC2Config.MSTSC_DIR)	
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
	checkDirectory(MarkLogicEC2Config.SESSION_DIR)		
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


def createPythonDownloadScript():	
	checkDirectory(MarkLogicEC2Config.POWERSHELL_DIR)
	fileName = MarkLogicEC2Config.POWERSHELL_DIR +"\\downloadpython.ps1"
	if not(os.path.isfile(fileName)):
		f = open(fileName,"w")
		f.write('$clnt = new-object System.Net.WebClient\n')
		f.write('$url = "'+MarkLogicEC2Config.PYTHON_DOWNLOAD_URL + MarkLogicEC2Config.PYTHON_EXE+'"\n')
		f.write('$file = "'+MarkLogicEC2Config.INSTALL_DIR+MarkLogicEC2Config.PYTHON_EXE+'"\n')
		f.write('$file\n')
		f.write('$clnt.DownloadFile($url,$file)\n')
		f.close()

def getPassword(host):
	password = ""
	if(MarkLogicEC2Config.MSTSC_PASSWORD):
		password = MarkLogicEC2Config.MSTSC_PASSWORD
	else:
		password = getDefaultPassword(host)
	return password


THAW_MODE = "thaw"
HELP_MODE = "help"
FREEZE_MODE  = "freeze"
STATUS_MODE = "status"
CLUSTER_MODE = "cluster"
CLEAN_MODE = "clean"
CREATE_MODE = "create"
SETUP_MODE = "setup"

MODES = (THAW_MODE,HELP_MODE,FREEZE_MODE,CLUSTER_MODE,CLEAN_MODE,CREATE_MODE,SETUP_MODE,STATUS_MODE)

# Get mode
if(len(sys.argv) > 1):
	mode = sys.argv[1]
else:
	mode = ""

print "Run mode is "+mode

if(mode == THAW_MODE):
	if(len(sys.argv) > 2):
		host = MarkLogicEC2Lib.getHostForRequest(sys.argv[2])
		startInstance(host)
	else:
		for host in getAvailableHosts():
			startInstance(host)
elif(mode == FREEZE_MODE):
	if(len(sys.argv) > 2):
		host = MarkLogicEC2Lib.getHostForRequest(sys.argv[2])
		stopInstance(host)
	else:
		for host in getAvailableHosts():
			stopInstance(host)
elif(mode == STATUS_MODE):
	if(len(sys.argv) > 2):
		host = MarkLogicEC2Lib.getHostForRequest(sys.argv[2])
		print "host "+host+ "is in the " + getInstanceStatus(host) + " state with dns " + getInstance(host).public_dns_name
	else:
		for host in getAvailableHosts():
			print "Host "+host+ "is in the " + getInstanceStatus(host) + " state with dns " + getInstance(host).public_dns_name
elif(mode == SETUP_MODE):
	if(len(sys.argv) > 2):
		host = MarkLogicEC2Lib.getHostForRequest(sys.argv[2])
		setupHost(host)
		MarkLogicEC2Lib.sys("Setting up "+host,"powershell -file pws\server-setup.ps1")		
	else:
		for host in getAvailableHosts():
			setupHost(host)			
			MarkLogicEC2Lib.sys("Setting up "+host,"powershell -file pws\server-setup.ps1")			
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
	clean()
elif(mode == CREATE_MODE):
	createHost()
elif(mode == "address"):	
	getRootElasticIP().associate(getAvailableHosts()[0])
else:
	print mode +" is not a permitted mode"
		
	

# Tasks
# Host Create
# Host setup
# Freeze
# Thaw

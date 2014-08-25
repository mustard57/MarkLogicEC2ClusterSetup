import MarkLogicEC2Lib
import MarkLogicEC2Config
import sys
import boto
import time
import os
import glob
import rsa
import re
import socket

SLEEP_PERIOD = 30
ec2 = boto.connect_ec2()

def getAvailableHosts():			
	hosts = []
	if(os.path.isfile(MarkLogicEC2Config.HOST_FILE)):
		f = open(MarkLogicEC2Config.HOST_FILE)
		for line in f.xreadlines():
			hosts.append(line.strip())
	return hosts

def getIPs():			
	ips = {}
	if(os.path.isfile(MarkLogicEC2Config.ELASTIC_IP_FILE)):
		f = open(MarkLogicEC2Config.ELASTIC_IP_FILE)
		for line in f.xreadlines():
			a = line.strip().split(",")
			ips[a[0]] = a[1]
	return ips
	
	
def getHostIP(host)	:
	return getIPs()[host]

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

def nameHost(host):	
	dns_name = getInstance(host).public_dns_name
	HOST_ARGS = { 'HOST-NAME':dns_name }
	MarkLogicEC2Lib.configureAuthHttpProcess(dns_name)
	MarkLogicEC2Lib.httpProcess("Setting host name",MarkLogicEC2Lib.adminURL(dns_name) +"set-host-name.xqy", HOST_ARGS)

def isRootHost(host):
	return os.path.isfile(MarkLogicEC2Config.HOST_FILE) and (len(getAvailableHosts()) > 0) and (getAvailableHosts()[0] == host)

def getElasticIP(host):
	address = ""
	for address in ec2.get_all_addresses():
		if address.public_ip == getHostIP(host):
			break
	return address				
	
def startInstance(host):
	if(not(isRunning(host))):
		print "Starting thaw of " + host + " at "+time.strftime("%H:%M:%S", time.gmtime())
		ec2.start_instances(host)
		waitForRunningState(host)
		if(MarkLogicEC2Config.USE_ELASTIC_IP):
			getElasticIP(host).associate(host)
			print "Elastic IP added for host " + host + " - " + str(getElasticIP(host))
		waitForReachableState(host)			
		if MarkLogicEC2Config.isRedHat():
			MarkLogicEC2Lib.sys("Check device mapping ...",sshToBoxString(getInstance(host).dns_name) + "'" + lnCommand()+ "'")			
			createSSHLink(host)
		if MarkLogicEC2Config.isWindows():
			createRDPLink(host)
			createSessionLink(host)
			createReinstallScript(host)					
		createAdminConsoleLink(host)
		
		print "Host " + host + " started at "+time.strftime("%H:%M:%S", time.gmtime())
	else:
		print "Host " + host + " already running"
		
def stopInstance(host):
	if(not(isStopped(host))):
		print "Stopping host "+host
		ec2.stop_instances(host)
		removeFile(RDPFileName(host))
		removeFile(adminFileName(host))
		removeFile(sessionFileName(host))
		removeFile(sshFileName(host))
		removeFile(reinstallFileName(host))
		waitForStoppedState(host)		
		print "Host stopped"				
	else:
		print "Host " + host + " already stopped"

def getInstance(host):
	while not(host in getInstances()):
		time.sleep(5)
	while not(ec2.get_all_instances(host)) :
		time.sleep(5)
	while not(ec2.get_all_instances(host)[0].instances) :
		time.sleep(5)
	return ec2.get_all_instances(host)[0].instances[0]

def getInstances():
	instances = []
	for i in ec2.get_all_instances():
		instances.append(str(i.instances[0].id))
	return instances

def getInstanceStatus(host):
	return getInstance(host).state

def isRunning(host):
	return getInstance(host).state == 'running' 

def isReachable(host):
	return getInstance(host).state == 'running' and ec2.get_all_instance_status(host)[0].instance_status.status == "ok" and ec2.get_all_instance_status(host)[0].system_status.status == "ok"

def isStopped(host):
	return getInstance(host).state == 'stopped'

def isTerminated(host):
	return getInstance(host).state == 'terminated'
	
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

def waitForReachableState(host):	
	while True:		
		instance = getInstance(host)
		if isReachable(host):
			break
		else:
			print "Instance not yet in reachable state"
		time.sleep(SLEEP_PERIOD)
		
def waitForStoppedState(host):	
	while True:		
		instance = getInstance(host)
		if isStopped(host):
			break
		else:
			print "Instance not yet in stopped state"
		time.sleep(SLEEP_PERIOD)

def waitForTerminatedState(host):	
	while True:		
		instance = getInstance(host)
		if isTerminated(host):
			break
		else:
			print "Instance not yet in terminated state"
		time.sleep(SLEEP_PERIOD)
		
def clean():
	if os.path.isfile(MarkLogicEC2Config.HOST_FILE):
		for host in getAvailableHosts():		
			cleanHost(host)	
	removeIPs()
	removeDirectories()	
	removeFile(MarkLogicEC2Config.HOST_FILE)
	removeFile(MarkLogicEC2Config.ELASTIC_IP_FILE)
	for file in glob.glob("*.pyc"):
		os.remove(file)

def cleanHost(host):
	print "Terminating host "+host
	dns_name = getInstance(host).public_dns_name	
	volumes_for_deletion = []

	# Get attached volumes before terminating - you can't get them after
	for volume in ec2.get_all_volumes():
#		print "Volume is "+volume.id
		if volume.attach_data.instance_id == host:
#			print "Adding "+volume.id
			volumes_for_deletion.append(volume.id)
			
	getInstance(host).terminate()
	
	waitForTerminatedState(host)
	
	# Now delete un-deleted volumes - problem with Red Hat instances is that they're not auto-deleted
	for volume in ec2.get_all_volumes():
		for volume_for_deletion in volumes_for_deletion:
			if volume.id == volume_for_deletion:			
				print "Removing volume " + volume.id
				volume.delete()
		
	if(MarkLogicEC2Config.USE_ELASTIC_IP):	
		if getElasticIP(host):		
			print "Removing elastic ip "+str(getElasticIP(host))
			getElasticIP(host).release()
	
	for file in (adminFileName(host),sessionFileName(host),reinstallFileName(host),RDPFileName(host),sshFileName(host)):
		removeFile(file)
	
	if(MarkLogicEC2Config.isRedHat()):
		MarkLogicEC2Lib.sys("Remove from known hosts file","ssh-keygen -R "+dns_name)
	
def clearDirectory(dirName):
	if os.path.isdir(dirName):
		for file in os.listdir(dirName):
			os.remove(dirName + "/" + file)

def removeDirectory(dirName):
	clearDirectory(dirName)
	if os.path.isdir(dirName):
		os.rmdir(dirName)
			
def checkDirectory(dirName):
	if not os.path.isdir(dirName):
		os.makedirs(dirName)

def removeDirectories():
	removeDirectory(MarkLogicEC2Config.POWERSHELL_DIR)
	removeDirectory(MarkLogicEC2Config.HTML_DIR)
	removeDirectory(MarkLogicEC2Config.MSTSC_DIR)
	removeDirectory(MarkLogicEC2Config.SESSION_DIR)

def removeIPs():
	for address in ec2.get_all_addresses():
		for ip in getIPs().values():
			if address.public_ip == ip:
				address.release()
				print ip + " removed"
	
def createHost():
	cmd=""

	print "Starting create host at "+time.strftime("%H:%M:%S", time.gmtime())
	
	if MarkLogicEC2Config.isWindows():
		cmd = '<powershell>Enable-PSRemoting -Force</powershell>'	
		
	reservation = ec2.run_instances(image_id=MarkLogicEC2Config.getImageID(),instance_type=MarkLogicEC2Config.INSTANCE_SIZE,key_name=MarkLogicEC2Config.EC2_KEY_PAIR_NAME,security_groups=[MarkLogicEC2Config.EC2_SECURITY_GROUP_NAME],user_data=cmd)
	
	instance = reservation.instances[0]
	print "Created instance "+ instance.id
	
	waitForRunningState(str(instance.id))

	f = open(MarkLogicEC2Config.HOST_FILE,"a")
	f.write(instance.id+"\n")
	f.close()	
	
	if(MarkLogicEC2Config.USE_ELASTIC_IP):
		allocateIP(instance.id)
		print "Elastic IP added for host " + instance.id + " - " + getHostIP(instance.id)

	waitForReachableState(str(instance.id))			
		
	if MarkLogicEC2Config.isRedHat():
		createSSHLink(str(instance.id))
		volume = ec2.create_volume(MarkLogicEC2Config.DISK_CAPACITY,instance.placement,"")
		while volume.status != 'available':
			print "Volume status is "+volume.status
			time.sleep(5)
			volume = ec2.get_all_volumes([str(volume.id)])[0]
		volume.attach(instance.id,MarkLogicEC2Config.EBS_DEVICE_NAME)
		print MarkLogicEC2Config.DISK_CAPACITY + "G disk volume created"
		print "Volume status is "+volume.status		
	print "Finishing create host at "+time.strftime("%H:%M:%S", time.gmtime())

		
def allocateIP(host):
	if(len(ec2.get_all_addresses()) >= MarkLogicEC2Config.EC2_ELASTIC_IP_LIMIT):
		print "You've used "+str(MarkLogicEC2Config.EC2_ELASTIC_IP_LIMIT)+" elastic IP addresses which is the limit. Configuring without elastic IP"
	else:
		ip = ec2.allocate_address() 	
		ec2.associate_address(instance_id=host,public_ip=ip.public_ip)
		print "Elastic IP "+ip.public_ip+" added"
		f = open(MarkLogicEC2Config.ELASTIC_IP_FILE,"a")
		f.write(host+","+ip.public_ip+"\n")
		f.close()	
	

def setupWindowsHost(host):
	instance = getInstance(host)

	dns_name =  instance.public_dns_name

	print "Starting "+dns_name+" setup at "+time.strftime("%H:%M:%S", time.gmtime())
	
	while True:		
		dns_name =  instance.public_dns_name
		instance_id =  instance.id
		ip  = repr(socket.gethostbyname(dns_name)).replace("'","")
		
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
	fileName = MarkLogicEC2Config.POWERSHELL_DIR  +"\\server-setup.ps1"
	if not(os.path.isfile(fileName)):	
		f = open(fileName,"w")
		f.write('echo "Setting up secure access via powershell"\n')
		f.write('Set-ItemProperty -Path HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -Name LocalAccountTokenFilterPolicy -Value 1 -Type DWord\n')
		f.write('Set-Item WSMan:\\localhost\\Client\TrustedHosts -Value ' + dns_name + " -Force\n")
		f.write("$pw = convertto-securestring -AsPlainText -Force -String '"+password+"'\n")
		f.write('$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist "'+instance_id+'\Administrator",$pw\n')
		f.write('$session = new-pssession -computername '+dns_name + ' -credential $cred\n')
		f.write('echo "Setting up access to remote file system - need to use ip address if not on same domain"\n')		
		f.write("net use \\\\"+ip+" '" + password + "' /user:Administrator\n")
		f.write('echo "Copying items required for setup"\n')
		f.write("copy-item -force -path for_remote\* -destination '\\\\"+ip+"\\"+MarkLogicEC2Config.INSTALL_DIR.replace(":","$")+"'\n")
		f.write("copy-item -force -path config.ini -destination '\\\\"+ip+"\\"+MarkLogicEC2Config.INSTALL_DIR.replace(":","$")+"'\n")
		f.write("copy-item -force -path MarkLogicEC2Config.py -destination '\\\\"+ip+"\\"+MarkLogicEC2Config.INSTALL_DIR.replace(":","$")+"'\n")
		f.write("copy-item -force -path MarkLogicEC2Lib.py -destination '\\\\"+ip+"\\"+MarkLogicEC2Config.INSTALL_DIR.replace(":","$")+"'\n")
		f.write('echo "Disable firewall - ftp will not run in ACTV mode with firewall enabled amongst other things"\n')
		f.write("invoke-command -session $session {netsh firewall set opmode disable disable}\n")		
		f.write('echo "Downloading python"\n')
		f.write("invoke-command -session $session -filepath pws\downloadpython.ps1\n")			
		f.write('echo "Downloading MarkLogic"\n')		
		f.write("invoke-command -session $session -filepath pws\downloadmarklogic.ps1\n")	
		f.write("sleep 30\n")
		f.write("echo 'installing python'\n")
		f.write("invoke-command -session $session {cd '" + MarkLogicEC2Config.INSTALL_DIR + "' ; " + ".\\"+MarkLogicEC2Config.PYTHON_EXE+" /passive /quiet}\n")	
		f.write("sleep 60\n")
		f.write("echo 'setting up MarkLogic'\n")
		f.write("invoke-command -session $session {cd '" + MarkLogicEC2Config.INSTALL_DIR + "' ; " + MarkLogicEC2Config.PYTHON_INSTALL_DIR + "\\python MarkLogicSetup.py}\n")
		f.write("invoke-command -session $session {Set-Service MarkLogic -startuptype 'Automatic'}\n")
		if(MarkLogicEC2Config.MSTSC_PASSWORD):
			#f.write('invoke-command -session $session {$account = [ADSI]("WinNT://$env:COMPUTERNAME/Administrator,user") ; $account.psbase.invoke("setpassword","'+MarkLogicEC2Config.MSTSC_PASSWORD+'") }\n')
			print "mstsc password will be set as requested"
		else:
			print "MSTSC password set not requested - will use password set by EC2"
		f.close()

	print dns_name
	createRDPLink(host)
	createAdminConsoleLink(host)
	createSessionLink(host)
	
	print "Finishing "+dns_name+" config at "+time.strftime("%H:%M:%S", time.gmtime())

def setupRedHatHost(host):
	instance = getInstance(host)
	dns_name =  instance.public_dns_name
	
	print "Starting "+dns_name+" setup at "+time.strftime("%H:%M:%S", time.gmtime())
	ssh_cmd = sshToBoxString(dns_name)

	MarkLogicEC2Lib.sys("Sort out device mapping ...",ssh_cmd + "'" + lnCommand() + "'")
	
	MarkLogicEC2Lib.sys("Remove host firewall",ssh_cmd+"'service iptables save ; service iptables stop ; chkconfig iptables off'")
	MarkLogicEC2Lib.sys("Download MarkLogic install",ssh_cmd + "'cd "+MarkLogicEC2Config.INSTALL_DIR+";curl -O "+MarkLogicEC2Config.MARKLOGIC_DOWNLOAD_URL + MarkLogicEC2Config.MARKLOGIC_EXE+"'")
	MarkLogicEC2Lib.sys("Copy required files","scp config.ini MarkLogicEC2Config.py MarkLogicEC2Lib.py for_remote/* root@"+dns_name+":"+MarkLogicEC2Config.INSTALL_DIR)
	MarkLogicEC2Lib.sys("Install MarkLogic",ssh_cmd+"\"cd "+MarkLogicEC2Config.INSTALL_DIR+";python MarkLogicSetup.py\"")
	
	createAdminConsoleLink(host)
	
	print "Finishing "+dns_name+" config at "+time.strftime("%H:%M:%S", time.gmtime())

def refreshRedHatHost(host):
	instance = getInstance(host)

	dns_name =  instance.public_dns_name
	ssh_cmd = sshToBoxString(dns_name)

	MarkLogicEC2Lib.sys("Stopping MarkLogic",ssh_cmd+"'/etc/init.d/MarkLogic stop'")
	MarkLogicEC2Lib.sys("Remove previous install",ssh_cmd+"\"rm -rf "+MarkLogicEC2Config.MARKLOGIC_REDHAT_DATA_ROOT +"/*\"")

	MarkLogicEC2Lib.sys("Install MarkLogic",ssh_cmd+"\"cd "+MarkLogicEC2Config.INSTALL_DIR+";python MarkLogicSetup.py\"")

	
	createAdminConsoleLink(host)

def setupHost(host):
	print "Setting up "+host
	if MarkLogicEC2Config.isWindows():
		setupWindowsHost(host)
		MarkLogicEC2Lib.sys("Setting up "+host,"powershell -file pws\server-setup.ps1")		
	elif MarkLogicEC2Config.isRedHat():
		setupRedHatHost(host)

def refreshHost(host):
	print "Starting refresh " + host + " at "+time.strftime("%H:%M:%S", time.gmtime())
	if MarkLogicEC2Config.isWindows():
		MarkLogicEC2Lib.sys("Reinstalling for "+host,"powershell -file " + reinstallFileName(host))		
	elif MarkLogicEC2Config.isRedHat():
		refreshRedHatHost(host)
	print "Finishing refresh " + host + " at "+time.strftime("%H:%M:%S", time.gmtime())

		
def cluster():	
	ROOT_HOST = ""
	print "Starting cluster at "+time.strftime("%H:%M:%S", time.gmtime())
	
	for host in getAvailableHosts():
		MarkLogicEC2Lib.configureAuthHttpProcess(getInstance(host).public_dns_name)	
		if ROOT_HOST:
			args = {'server' : ROOT_HOST, 'joiner' : getInstance(host).public_dns_name, 'pass' : MarkLogicEC2Config.ADMIN_PASSWORD }
			
			MarkLogicEC2Lib.httpProcess("Joining Cluster","http://" + getInstance(host).public_dns_name + ":8001/join-cluster.xqy", args)
		else:
			ROOT_HOST = getInstance(host).public_dns_name

	ROOT_HOST = ""

	for host in getAvailableHosts():
		if ROOT_HOST:
			args = {'server' : ROOT_HOST, 'joiner' : getInstance(host).public_dns_name, 'pass' : MarkLogicEC2Config.ADMIN_PASSWORD}
			MarkLogicEC2Lib.configureAuthHttpProcess(ROOT_HOST)
			MarkLogicEC2Lib.httpProcess("Joining Cluster II","http://" + ROOT_HOST + ":8001/transfer-cluster-config.xqy",args)
			MarkLogicEC2Lib.configureAuthHttpProcess(getInstance(host).public_dns_name)
			MarkLogicEC2Lib.httpProcess("Restarting...","http://" + getInstance(host).public_dns_name + ":8001/restart.xqy")
		else:
			ROOT_HOST = getInstance(host).public_dns_name

	MarkLogicEC2Lib.configureAuthHttpProcess(ROOT_HOST)
	MarkLogicEC2Lib.httpProcess("Setting cluster name to "+MarkLogicEC2Config.CLUSTER_NAME,"http://" + ROOT_HOST + ":8001/set-cluster-name.xqy",{"CLUSTER-NAME":MarkLogicEC2Config.CLUSTER_NAME})	
	print "Finishing cluster at "+time.strftime("%H:%M:%S", time.gmtime())

	
def createMarkLogicDownloadScript():
	checkDirectory(MarkLogicEC2Config.POWERSHELL_DIR)
	fileName = MarkLogicEC2Config.POWERSHELL_DIR +"\\downloadmarklogic.ps1"
	if not(os.path.isfile(fileName)):
		f = open(fileName,"w")
		f.write('$clnt = new-object System.Net.WebClient\n')
		f.write('$url = "'+MarkLogicEC2Config.MARKLOGIC_DOWNLOAD_URL + MarkLogicEC2Config.MARKLOGIC_EXE+'"\n')		
		f.write('$file = "'+MarkLogicEC2Config.INSTALL_DIR + MarkLogicEC2Config.MARKLOGIC_EXE+'"\n')
		# f.write('$uri = New-Object System.Uri($url)\n')		
		f.write('$clnt.DownloadFile($url,$file)\n')
		f.close()

def createAdminConsoleLink(host):
	dns_name = getInstance(host).public_dns_name	
	f = open(adminFileName(host),"w")
	f.write("<html><head><script>window.location = 'http://" + dns_name +":8001';</script></head><body></body></html>")
	f.close()
	
def createRDPLink(host):
	dns_name = getInstance(host).public_dns_name	
	f = open(RDPFileName(host),"w")
	f.write("auto connect:i:1\n")
	f.write("full address:s:"+dns_name+"\n")
	f.write("username:s:Administrator\n")
	f.close()
	
def createSessionLink(host):	
	dns_name = getInstance(host).public_dns_name	
	password = getPassword(host)
	instance_id = getInstance(host).id
	f = open(sessionFileName(host),"w")
	f.write('Set-ItemProperty -Path HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -Name LocalAccountTokenFilterPolicy -Value 1 -Type DWord\n')
	f.write('Set-Item WSMan:\\localhost\\Client\TrustedHosts -Value ' + dns_name + " -Force -Concatenate\n")
	f.write("$pw = convertto-securestring -AsPlainText -Force -String '"+password+"'\n")
	f.write('$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist "'+instance_id+'\Administrator",$pw\n')
	f.write('$session = new-pssession -computername '+dns_name + ' -credential $cred\n')
	f.write('Enter-PSSession $session\n')
	f.close()

def createSSHLink(host):
	dns_name = getInstance(host).public_dns_name	
	f = open(sshFileName(host),"w")
	f.write(sshToBoxString(dns_name))
	f.close()
	
def createReinstallScript(host):	
	dns_name = getInstance(host).public_dns_name	
	password = getPassword(host)
	instance_id = getInstance(host).id
	f = open(reinstallFileName(host),"w")
	f.write('Set-ItemProperty -Path HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -Name LocalAccountTokenFilterPolicy -Value 1 -Type DWord\n')
	f.write('Set-Item WSMan:\\localhost\\Client\TrustedHosts -Value ' + dns_name + " -Force -Concatenate\n")
	f.write("$pw = convertto-securestring -AsPlainText -Force -String '"+password+"'\n")
	f.write('$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist "'+instance_id+'\Administrator",$pw\n')
	f.write('$session = new-pssession -computername '+dns_name + ' -credential $cred\n')
	f.write('echo "Reinstalling MarkLogic"\n')
	f.write('invoke-command -session $session {net stop MarkLogic}\n')
	f.write('invoke-command -session $session {cd "c:\program files\MarkLogic\Data"}\n')
	f.write('invoke-command -session $session {Remove-Item *.xml}\n')
	f.write('invoke-command -session $session {Remove-Item  Forests -recurse}\n')
	f.write('invoke-command -session $session {cd c:\users\\administrator\ ; c:\python26\python MarkLogicSetup.py}\n')	
	f.write("invoke-command -session $session {Set-Service MarkLogic -startuptype 'Automatic'}\n")
	f.close()

def createPythonDownloadScript():	
	checkDirectory(MarkLogicEC2Config.POWERSHELL_DIR)
	fileName = MarkLogicEC2Config.POWERSHELL_DIR +"\\downloadpython.ps1"
	if not(os.path.isfile(fileName)):
		f = open(fileName,"w")
		f.write('$clnt = new-object System.Net.WebClient\n')
		f.write('$url = "'+MarkLogicEC2Config.PYTHON_DOWNLOAD_URL + MarkLogicEC2Config.PYTHON_EXE+'"\n')
		f.write('$file = "'+MarkLogicEC2Config.INSTALL_DIR+MarkLogicEC2Config.PYTHON_EXE+'"\n')
		f.write('$clnt.DownloadFile($url,$file)\n')
		f.close()

def getPassword(host):
	password = ""
	if(MarkLogicEC2Config.MSTSC_PASSWORD):
		password = MarkLogicEC2Config.MSTSC_PASSWORD
	else:
		password = getDefaultPassword(host)
	return password

def utilityFileName(dir,host,suffix):
	checkDirectory(dir)
	return dir  +"\\"+getInstance(host).public_dns_name+"."+ suffix

def adminFileName(host):
	return utilityFileName(MarkLogicEC2Config.HTML_DIR,host,"admin.html")

def RDPFileName(host):
	return utilityFileName(MarkLogicEC2Config.MSTSC_DIR,host,"rdp")

def sessionFileName(host):
	return utilityFileName(MarkLogicEC2Config.SESSION_DIR,host,"session.ps1")

def sshFileName(host):
	return utilityFileName(MarkLogicEC2Config.SESSION_DIR,host,"ssh.sh")
	
def reinstallFileName(host):
	return utilityFileName(MarkLogicEC2Config.POWERSHELL_DIR,host,"reinstall.ps1")

def removeFile(fileName):
	if os.path.isfile(fileName):
		os.remove(fileName)

def sshToBoxString(dns_name):
	return "ssh -o StrictHostKeyChecking=no root@"+dns_name+" "

def lnCommand():
	return "ln "+MarkLogicEC2Config.ACTUAL_EBS_DEVICE_NAME+" "+MarkLogicEC2Config.EXPECTED_EBS_DEVICE_NAME	

def restartHost(host):
	if(MarkLogicEC2Config.isRedHat()):
		MarkLogicEC2Lib.sys("Restarting "+host,sshToBoxString(getInstance(host).dns_name) + "'/etc/init.d/MarkLogic restart'")
	
THAW_MODE = "thaw"
HELP_MODE = "help"
FREEZE_MODE  = "freeze"
STATUS_MODE = "status"
CLUSTER_MODE = "cluster"
CLEAN_MODE = "clean"
CREATE_MODE = "create"
SETUP_MODE = "setup"
REFRESH_MODE = "refresh"
RESTART_MODE = "restart"
DEVICES_MODE = "devices"
REMOTE_MODE="remote"
ALL_MODE = "all"

MODES = (THAW_MODE,HELP_MODE,FREEZE_MODE,CLUSTER_MODE,CLEAN_MODE,CREATE_MODE,SETUP_MODE,STATUS_MODE,REFRESH_MODE,ALL_MODE,RESTART_MODE,DEVICES_MODE,REMOTE_MODE)

# Get mode
if(len(sys.argv) > 1):
	mode = sys.argv[1]
else:
	mode = ""

print "Run mode is "+mode

if(mode == THAW_MODE):
	if(len(sys.argv) > 2):
		host = getHostForRequest(sys.argv[2])
		startInstance(host)
	else:
		for host in getAvailableHosts():
			startInstance(host)
elif(mode == FREEZE_MODE):
	if(len(sys.argv) > 2):
		host = getHostForRequest(sys.argv[2])
		stopInstance(host)
	else:
		for host in getAvailableHosts():
			stopInstance(host)
elif(mode == STATUS_MODE):
	if(len(sys.argv) > 2):
		host = getHostForRequest(sys.argv[2])
		print "host "+host+ "is in the " + getInstanceStatus(host) + " state with dns = " + (getInstance(host).public_dns_name if getInstance(host).public_dns_name else "None")
	else:
		for host in getAvailableHosts():
			print "Host "+host+ "is in the " + getInstanceStatus(host) + " state with dns = " + (getInstance(host).public_dns_name if getInstance(host).public_dns_name else "None")
elif(mode == SETUP_MODE):
	if(len(sys.argv) > 2):
		host = getHostForRequest(sys.argv[2])
		setupHost(host)
	else:
		for host in getAvailableHosts():
			setupHost(host)
elif(mode == HELP_MODE):		
	print "Available modes are "+",".join(MODES)
elif(mode == CLUSTER_MODE):
	cluster()
elif(mode == CLEAN_MODE):
	if(len(sys.argv) > 2):
		host = getHostForRequest(sys.argv[2])
		cleanHost(host)
	else:
		clean()
elif(mode == CREATE_MODE):
	if(len(sys.argv) > 2):
		for i in range(int(sys.argv[2])):
			createHost()
	else:
		createHost()
elif(mode == REFRESH_MODE):
	if(len(sys.argv) > 2):
		host = getHostForRequest(sys.argv[2])
		refreshHost(host)
	else:
		for host in getAvailableHosts():
			refreshHost(host)			
elif(mode == ALL_MODE):
	for i in range(MarkLogicEC2Config.HOST_COUNT):
		createHost()
	for host in getAvailableHosts():
		setupHost(host)			
	cluster()
elif(mode == RESTART_MODE):
	if(len(sys.argv) > 2):
		host = getHostForRequest(sys.argv[2])
		restartHost(host)
	else:
		for host in getAvailableHosts():
			restartHost(host)			
elif(mode == DEVICES_MODE):
	if(len(sys.argv) > 2):
		host = getHostForRequest(sys.argv[2])
		MarkLogicEC2Lib.sys("Check device mapping ...",sshToBoxString(getInstance(host).dns_name) + "'" + lnCommand()+ "'")						
	else:
		for host in getAvailableHosts():
			MarkLogicEC2Lib.sys("Check device mapping ...",sshToBoxString(getInstance(host).dns_name) + "'" + lnCommand()+ "'")												
elif(mode == REMOTE_MODE):
	if(len(sys.argv) > 2):			
		dns_name =  getInstance(getHostForRequest(sys.argv[2])).dns_name
		if MarkLogicEC2Config.isRedHat():
			MarkLogicEC2Lib.sys("Logging into box "+dns_name,sshToBoxString(dns_name))
		elif MarkLogicEC2Config.isWindows():
			MarkLogicEC2Lib.sys("Logging into box "+dns_name,"powershell -noexit -file sessions\\"+ dns_name + ".session.ps1")
	else:
		print "You must supply an index or an instance id"
else:
	print mode +" is not a permitted mode"
		
	


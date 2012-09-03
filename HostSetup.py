import boto
import rsa
import os
import sys
import time
import MarkLogicEC2Config
import MarkLogicEC2Lib

def get_instance(instance_id):
	instance=None
	for i in ec2.get_all_instances():
		if i.instances[0].id == instance_id:
			instance = i.instances[0]
	return instance
	
HOST_NAME = sys.argv[1]

# Constants
SLEEP_PERIOD = 30

# Set up powershell dir
MarkLogicEC2Lib.checkDirectories()

dns_name = instance_id = password = ""

# EC2 connection 
ec2 = boto.connect_ec2()
print "Connecting to EC2 at "+time.strftime("%H:%M:%S", time.gmtime())

# Get Instance, DNS name, instance id
instance = get_instance(HOST_NAME)

if not instance:
	print HOST_NAME + "does not exist"
else:
	print HOST_NAME + " exists and is in state " + instance.state

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

print "Creating config for " + dns_name

# Create download Python script
f = open(MarkLogicEC2Config.POWERSHELL_DIR +"\\downloadpython.ps1","w")
f.write('$clnt = new-object System.Net.WebClient\n')
f.write('$url = "'+MarkLogicEC2Config.PYTHON_DOWNLOAD_URL + MarkLogicEC2Config.PYTHON_EXE+'"\n')
f.write('$file = "'+MarkLogicEC2Config.INSTALL_DIR+MarkLogicEC2Config.PYTHON_EXE+'"\n')
f.write('$file\n')
f.write('$clnt.DownloadFile($url,$file)\n')
f.close()

# Create download MarkLogic script
f = open(MarkLogicEC2Config.POWERSHELL_DIR + "\\downloadmarklogic.ps1","w")
f.write('$clnt = new-object System.Net.WebClient\n')
f.write('$url = "'+MarkLogicEC2Config.MARKLOGIC_DOWNLOAD_URL + MarkLogicEC2Config.MARKLOGIC_EXE+'"\n')
f.write('$file = "'+MarkLogicEC2Config.INSTALL_DIR + MarkLogicEC2Config.MARKLOGIC_EXE+'"\n')
f.write('$file\n')
f.write('$clnt.DownloadFile($url,$file)\n')
f.close()

# Create server setup script
f = open(MarkLogicEC2Config.POWERSHELL_DIR  +"\\server-setup.ps1","w")
f.write('Set-ItemProperty -Path HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -Name LocalAccountTokenFilterPolicy -Value 1 -Type DWord\n')
f.write('Set-Item WSMan:\\localhost\\Client\TrustedHosts -Value ' + dns_name + " -Force -Concatenate\n")
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
f.write("invoke-command -session $session {netsh firewall set opmode disable}\n")
if(MarkLogicEC2Config.MSTSC_PASSWORD):
	f.write('invoke-command -session $session {$account = [ADSI]("WinNT://$env:COMPUTERNAME/Administrator,user") ; $account.psbase.invoke("setpassword","'+MarkLogicEC2Config.MSTSC_PASSWORD+'") }\n')
	print "Setting mstsc password as requested"
else:
	print "MSTSC password set not requested - will use password set by EC2"
f.close()

# Create admin console link
f = open(MarkLogicEC2Config.HTML_DIR + "\\" + dns_name + ".admin.html","w")
f.write("<html><head><script>window.location = 'http://" + dns_name +":8001';</script></head><body></body></html>")
f.close()

# Create rdp link
f = open(MarkLogicEC2Config.MSTSC_DIR + "\\" + dns_name + ".rdp","w")
f.write("auto connect:i:1\n")
f.write("full address:s:"+dns_name+"\n")
f.write("username:s:Administrator\n")
f.close()

# Create server setup script
f = open(MarkLogicEC2Config.SESSION_DIR  +"\\"+dns_name+".session.ps1","w")
f.write('Set-ItemProperty -Path HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -Name LocalAccountTokenFilterPolicy -Value 1 -Type DWord\n')
f.write('Set-Item WSMan:\\localhost\\Client\TrustedHosts -Value ' + dns_name + " -Force -Concatenate\n")
f.write("$pw = convertto-securestring -AsPlainText -Force -String '"+password+"'\n")
f.write('$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist "'+instance_id+'\Administrator",$pw\n')
f.write('$session = new-pssession -computername '+dns_name + ' -credential $cred\n')
f.write('Enter-PSSession $session\n')
f.close()

print "Finishing "+dns_name+" config at "+time.strftime("%H:%M:%S", time.gmtime())

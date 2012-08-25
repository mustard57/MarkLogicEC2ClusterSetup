import boto
import rsa
import ConfigParser
import os

# Constants
POWERSHELL_DIR = "pws"

# Configuration
CONFIG_FILE="config.ini"
                                     									 
parser = ConfigParser.ConfigParser()
parser.read(CONFIG_FILE)

MARKLOGIC_EXE = parser.get("Software","MARKLOGIC_EXE")
MARKLOGIC_DOWNLOAD_URL=parser.get("Software","MARKLOGIC_DOWNLOAD_URL")
PYTHON_DOWNLOAD_URL=parser.get("Software","PYTHON_DOWNLOAD_URL")
PYTHON_EXE=parser.get("Software","PYTHON_EXE")
PYTHON_INSTALL_DIR=parser.get("Software","PYTHON_INSTALL_DIR")
INSTALL_DIR=parser.get("Configuration","INSTALL_DIR")
RSA_PRIVATE_KEY=parser.get("Configuration","RSA_PRIVATE_KEY")

# Set up powershell dir
if not os.path.isdir(POWERSHELL_DIR):
	os.makedirs(POWERSHELL_DIR)
	
# Which Instance do you want? 
instance_no = -1

# EC2 connection 
ec2 = boto.connect_ec2()

# Get Instance, DNS name, instance id
instance = ec2.get_all_instances()[instance_no].instances[0]
dns_name =  instance.public_dns_name
instance_id =  instance.id

# Get Encrypted password
encrypted_pword = ec2.get_password_data(instance.id).strip("\n\r\t").decode('base64')

with open(RSA_PRIVATE_KEY) as privatefile:
	keydata = privatefile.read()
privkey = rsa.PrivateKey.load_pkcs1(keydata)

# Get decrypted password
if encrypted_pword:
	password = rsa.decrypt(encrypted_pword,privkey)
else:
	password = "No password available yet"


# Create download Python script
f = open(POWERSHELL_DIR +"\\downloadpython.ps1","w")
f.write('$clnt = new-object System.Net.WebClient\n')
f.write('$url = "'+PYTHON_DOWNLOAD_URL + PYTHON_EXE+'"\n')
f.write('$file = "'+INSTALL_DIR+PYTHON_EXE+'"\n')
f.write('$file\n')
f.write('$clnt.DownloadFile($url,$file)\n')
f.close()

# Create download MarkLogic script
f = open(POWERSHELL_DIR + "\\downloadmarklogic.ps1","w")
f.write('$clnt = new-object System.Net.WebClient\n')
f.write('$url = "'+MARKLOGIC_DOWNLOAD_URL + MARKLOGIC_EXE+'"\n')
f.write('$file = "'+INSTALL_DIR + MARKLOGIC_EXE+'"\n')
f.write('$file\n')
f.write('$clnt.DownloadFile($url,$file)\n')
f.close()

# Create server setup script
f = open(POWERSHELL_DIR  +"\\server-setup.ps1","w")
f.write('Set-ItemProperty -Path HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -Name LocalAccountTokenFilterPolicy -Value 1 -Type DWord\n')
f.write('Set-Item WSMan:\\localhost\\Client\TrustedHosts -Value ' + dns_name + " -Force -Concatenate\n")
f.write('$pw = convertto-securestring -AsPlainText -Force -String '+password+'\n')
f.write('$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist "'+instance_id+'\Administrator",$pw\n')
f.write('$session = new-pssession -computername '+dns_name + ' -credential $cred\n')
f.write("net use \\\\"+dns_name+" " + password + " /user:Administrator\n")
f.write("copy-item -force -path for_remote\* -destination \\\\"+dns_name+"\\"+INSTALL_DIR.replace(":","$")+"\n")
f.write("copy-item -force -path config.ini -destination \\\\"+dns_name+"\\"+INSTALL_DIR.replace(":","$")+"\n")
f.write("invoke-command -session $session -filepath pws\downloadpython.ps1\n")	
# f.write("invoke-command -session $session -filepath pws\downloadmarklogic.ps1\n")	
f.write("invoke-command -session $session {"+ INSTALL_DIR + PYTHON_EXE+"}\n")	
f.write("invoke-command -session $session {cd " + INSTALL_DIR + " ; " + PYTHON_INSTALL_DIR + "\\python MarkLogicSetup.py}")
f.close()


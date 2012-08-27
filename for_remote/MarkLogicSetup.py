import os
import sys
import subprocess
import shlex
import time
import urllib.request, urllib.parse, urllib.error
import configparser
                                     
"""
	Generic MarkLogic install and configuration script     
    	author: Alex Bleasdale <ableasdale@marklogic.com> 
		updated: Ken Tune <ken.tune@marklogic.com>
	version: 0.2

	Requires Python 3.0 ( Written using Python 3.2 ) 
"""

CONFIG_FILE="config.ini"
                                     									 
parser = configparser.ConfigParser()
parser.read(CONFIG_FILE)

LICENSE_KEY = parser.get("License Details","LICENSE_KEY")
LICENSEE = parser.get("License Details","LICENSEE")
ACCEPTED_AGREEMENT = parser.get("License Details","LICENSE_TYPE")

MARKLOGIC_EXE = parser.get("Software","MARKLOGIC_EXE")
INSTALL_DIR=parser.get("Configuration","INSTALL_DIR")

MARKLOGIC_ROOT = parser.get("Software","MARKLOGIC_INSTALL_DIR")								 
ADMIN_ROOT = MARKLOGIC_ROOT + "Admin\\"

INSTALL_MODE= " /passive /quiet"

INSTALL_CMD = INSTALL_DIR + MARKLOGIC_EXE + INSTALL_MODE

ADM_UNAME = "admin"
ADM_PASSWORD = "admin"
 
BASE_HREF = "http://localhost:8001/"
BASE_XDBC_PORT = "9999"
 
LICENCE_ARGS = { 'license-key':LICENSE_KEY, 'licensee':LICENSEE }
SECURITY_ARGS = { 'auto':'true', 'user':ADM_UNAME, 'password1':ADM_PASSWORD, 'password2':ADM_PASSWORD, 'realm':'public' }
EULA_ARGS = { 'accepted-agreement':ACCEPTED_AGREEMENT,"ok.x":1 }
 
BOOSTER_LATEST = "http://booster-xqy.googlecode.com/files/booster-0.2.xqy"
EC2_RESOLUTION_URL = "http://169.254.169.254/2009-04-04/meta-data/public-hostname"

BOOSTER_XDBC_ARGS = {
        'action':'appserver-create-xdbc',
        'appserver-name':'xdbc-' + BASE_XDBC_PORT,
        'database-name':'Documents',
        'group-name':'Default',
        'modules-name':'Modules',
        'root':'/',
        'port':BASE_XDBC_PORT
}

def getEC2Name():
	request = urllib.request.Request(EC2_RESOLUTION_URL)
	response = urllib.request.urlopen(request)	
	data = response.read().decode()	
	return data
 
def httpProcess(message, url, args = "", debug = False):
	print(message)
	request = urllib.request.Request(BASE_HREF + url)
	if args == "":
		response = urllib.request.urlopen(request)	
	else:
		response = urllib.request.urlopen(request, urllib.parse.urlencode(args).encode())
	if (debug == True):
		data = response.read()
		print(data)
 
def configureAuthHttpProcess():
	passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()	
	passman.add_password(None, BASE_HREF, ADM_UNAME, ADM_PASSWORD)	
	authhandler = urllib.request.HTTPDigestAuthHandler(passman)
	opener = urllib.request.build_opener(authhandler)
	urllib.request.install_opener(opener)
 
def sys(message, cmd):
	print(message)
	print(cmd)
	os.system(cmd)
	time.sleep(10)
 
def checkRootUser():
	if os.geteuid() != 0:
		print("Please execute this script as root!")
	sys.exit(1)


 
configureAuthHttpProcess()
sys("2. Installing", INSTALL_CMD)
sys("3. Starting MarkLogic Instance", "net start MarkLogic")
httpProcess("4. Configuring licence details", "license-go.xqy", LICENCE_ARGS)
httpProcess("5. Accepting EULA", "agree-go.xqy", EULA_ARGS)
httpProcess("6. Triggering initial application server config", "initialize-go.xqy")
sys("7a. Restarting Server", "net stop MarkLogic")
sys("7b. Restarting Server", "net start MarkLogic")
httpProcess("8. Configuring Admin user (security)", "security-install-go.xqy", SECURITY_ARGS)
httpProcess("9. Testing Admin Connection", "default.xqy")
#	sys("10. Getting booster.xqy from googlecode", "wget " + BOOSTER_LATEST)
#	sys("11. Moving booster to ML Admin", "mv booster-0.2.xqy /opt/MarkLogic/Admin/booster.xqy")
#	httpProcess("12. Configuring XDBC Server on port " + BASE_XDBC_PORT, "booster.xqy", BOOSTER_XDBC_ARGS)
#	sys("12. Cleaning up", "rm " + BINARY_FILENAME)
sys("Move set host name script","copy /Y *.xqy \""+ADMIN_ROOT+"\"")
HOST_ARGS = { 'HOST-NAME':getEC2Name() }
httpProcess("Setting host name","set-host-name.xqy", HOST_ARGS)
sys("Remove set host name script","del \""+ADMIN_ROOT+"set-host-name.xqy\"")
print("Script completed, visit http://"+getEC2Name()+":8001 to access the admin interface.")



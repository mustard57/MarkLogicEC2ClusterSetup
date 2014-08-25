import os
import sys
import urllib
import urllib2
import MarkLogicEC2Config
from MarkLogicEC2Config import LICENSE_KEY,LICENSEE,ACCEPTED_AGREEMENT,MARKLOGIC_EXE,INSTALL_DIR,MARKLOGIC_ROOT,ADMIN_USER_NAME,ADMIN_PASSWORD
from MarkLogicEC2Lib import sys,configureAuthHttpProcess,httpProcess,getEC2Name
                                     
"""
	Generic MarkLogic install and configuration script     
    	author: Alex Bleasdale <ableasdale@marklogic.com> 
		updated: Ken Tune <ken.tune@marklogic.com>
	version: 0.2

"""

ADMIN_ROOT = MARKLOGIC_ROOT + "Admin\\"
WINDOWS_INSTALL_MODE= " /passive /quiet"

INSTALL_CMD=""
START_CMD=""
STOP_CMD=""

if MarkLogicEC2Config.isWindows():
	INSTALL_CMD = '"'+INSTALL_DIR + MARKLOGIC_EXE +'"' + WINDOWS_INSTALL_MODE
	START_CMD = "net start MarkLogic"
	STOP_CMD = "net stop MarkLogic"
	ADMIN_ROOT = MARKLOGIC_ROOT + "Admin\\"
	COPY_CMD = "copy /Y *.xqy \""+ADMIN_ROOT+"\""

elif MarkLogicEC2Config.isRedHat():
	INSTALL_CMD = "cd " + INSTALL_DIR +"; yum -y install "+ MARKLOGIC_EXE
	START_CMD = "/etc/init.d/MarkLogic start"
	STOP_CMD = "/etc/init.d/MarkLogic stop"
	ADMIN_ROOT = MARKLOGIC_ROOT + "Admin/"
	COPY_CMD = "cp *.xqy "+ADMIN_ROOT

	
LOCALHOST = "localhost" 
BASE_HREF = "http://" + LOCALHOST + ":8001/"
 
LICENCE_ARGS = { 'license-key':LICENSE_KEY, 'licensee':LICENSEE }
SECURITY_ARGS = { 'auto':'true', 'user':ADMIN_USER_NAME, 'password1':ADMIN_PASSWORD, 'password2':ADMIN_PASSWORD, 'realm':'public' }
EULA_ARGS = { 'accepted-agreement':ACCEPTED_AGREEMENT,"ok.x":1 }
   
def checkRootUser():
	if os.geteuid() != 0:
		print("Please execute this script as root!")
	sys.exit(1)
 
configureAuthHttpProcess(LOCALHOST)
sys("2. Installing", INSTALL_CMD)
sys("3. Starting MarkLogic Instance", START_CMD)
httpProcess("4. Configuring licence details", BASE_HREF + "license-go.xqy", LICENCE_ARGS)
httpProcess("5. Accepting EULA", BASE_HREF +"agree-go.xqy", EULA_ARGS)
httpProcess("6. Triggering initial application server config", BASE_HREF +"initialize-go.xqy")
sys("7a. Restarting Server", STOP_CMD)
sys("7b. Restarting Server", START_CMD)
httpProcess("8. Configuring Admin user (security)", BASE_HREF +"security-install-go.xqy", SECURITY_ARGS)
httpProcess("9. Testing Admin Connection", BASE_HREF +"default.xqy")
sys("Move set host name script",COPY_CMD)
HOST_ARGS = { 'HOST-NAME':getEC2Name() }
httpProcess("Setting host name",BASE_HREF +"set-host-name.xqy", HOST_ARGS)
print("Script completed, visit http://"+getEC2Name()+":8001 to access the admin interface.")



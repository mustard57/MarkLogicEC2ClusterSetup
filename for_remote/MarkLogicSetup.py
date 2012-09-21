import os
import sys
import urllib
import urllib2
from MarkLogicEC2Config import LICENSE_KEY,LICENSEE,ACCEPTED_AGREEMENT,MARKLOGIC_EXE,INSTALL_DIR,MARKLOGIC_ROOT,ADMIN_USER_NAME,ADMIN_PASSWORD
from MarkLogicEC2Lib import sys,configureAuthHttpProcess,httpProcess,getEC2Name
                                     
"""
	Generic MarkLogic install and configuration script     
    	author: Alex Bleasdale <ableasdale@marklogic.com> 
		updated: Ken Tune <ken.tune@marklogic.com>
	version: 0.2

"""

ADMIN_ROOT = MARKLOGIC_ROOT + "Admin\\"
INSTALL_MODE= " /passive /quiet"
INSTALL_CMD = INSTALL_DIR + MARKLOGIC_EXE + INSTALL_MODE

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
sys("3. Starting MarkLogic Instance", "net start MarkLogic")
httpProcess("4. Configuring licence details", BASE_HREF + "license-go.xqy", LICENCE_ARGS)
httpProcess("5. Accepting EULA", BASE_HREF +"agree-go.xqy", EULA_ARGS)
httpProcess("6. Triggering initial application server config", BASE_HREF +"initialize-go.xqy")
sys("7a. Restarting Server", "net stop MarkLogic")
sys("7b. Restarting Server", "net start MarkLogic")
httpProcess("8. Configuring Admin user (security)", BASE_HREF +"security-install-go.xqy", SECURITY_ARGS)
httpProcess("9. Testing Admin Connection", BASE_HREF +"default.xqy")
sys("Move set host name script","copy /Y *.xqy \""+ADMIN_ROOT+"\"")
HOST_ARGS = { 'HOST-NAME':getEC2Name() }
httpProcess("Setting host name",BASE_HREF +"set-host-name.xqy", HOST_ARGS)
print("Script completed, visit http://"+getEC2Name()+":8001 to access the admin interface.")



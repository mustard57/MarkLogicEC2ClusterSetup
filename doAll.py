import os
import sys
import ConfigParser
import time

def sys(message, cmd):
	print(message)
	os.system(cmd)
	time.sleep(10)


# Configuration
CONFIG_FILE="config.ini"
                                     									 
parser = ConfigParser.ConfigParser()
parser.read(CONFIG_FILE)

HOST_FILE = parser.get("Constants","HOST_FILE")

f = open(HOST_FILE)

for line in f.xreadlines():
	host =  line.strip()
	sys("Setting up config for "+host,"python HostSetup.py "+host)
	sys("Setting up "+host,"powershell -file pws\server-setup.ps1")
	
sys("Configuring cluster","python doClusterStuff.py")
	

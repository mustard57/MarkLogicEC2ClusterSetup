from MarkLogicEC2Config import HOST_FILE
from MarkLogicEC2Lib import sys

f = open(HOST_FILE)

for line in f.xreadlines():
	host =  line.strip()
	sys("Setting up config for "+host,"python HostSetup.py "+host)
	sys("Setting up "+host,"powershell -file pws\server-setup.ps1")
	
sys("Configuring cluster","python doClusterStuff.py")
	

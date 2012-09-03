from MarkLogicEC2Config import HOST_FILE
import MarkLogicEC2Lib

# Clear out powershell/html/mstsc directories
MarkLogicEC2Lib.clearDirectories()

f = open(HOST_FILE)

for line in f.xreadlines():
	host =  line.strip()
	MarkLogicEC2Lib.sys("Setting up config for "+host,"python HostSetup.py "+host)
	MarkLogicEC2Lib.sys("Setting up "+host,"powershell -file pws\server-setup.ps1")
	
MarkLogicEC2Lib.sys("Configuring cluster","python doClusterStuff.py")
	

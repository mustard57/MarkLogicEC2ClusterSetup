import MarkLogicEC2Lib 
import MarkLogicEC2Config
import os
import glob

MarkLogicEC2Lib.clearDirectories
if os.path.isfile(MarkLogicEC2Config.HOST_FILE):
	os.remove(MarkLogicEC2Config.HOST_FILE)
for file in glob.glob("*.pyc"):
	os.remove(file)


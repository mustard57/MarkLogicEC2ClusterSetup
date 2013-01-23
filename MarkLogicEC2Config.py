import ConfigParser
import os

# Configuration
CONFIG_FILE="config.ini"

# Constants
HTML_DIR="html"
MSTSC_DIR="mstsc"
POWERSHELL_DIR = "pws"
SESSION_DIR = "sessions"

REDHAT_INSTANCE_TYPE = "RedHat"
WINDOWS_INSTANCE_TYPE = "Windows"

PERMITTED_INSTANCE_TYPES = [REDHAT_INSTANCE_TYPE,WINDOWS_INSTANCE_TYPE]
                                     
if not(os.path.isfile(CONFIG_FILE)):
	print "Config file " + CONFIG_FILE + " not found. Copy config.ini.sample -> config.ini and edit"
	exit()
									 
parser = ConfigParser.ConfigParser()
parser.read(CONFIG_FILE)

INSTANCE_TYPE=parser.get("Configuration","INSTANCE_TYPE")

def isWindows():
	return True if (INSTANCE_TYPE == WINDOWS_INSTANCE_TYPE) else False

def isRedHat():
	return True if (INSTANCE_TYPE == REDHAT_INSTANCE_TYPE) else False

def checkOS():
	if not(INSTANCE_TYPE in PERMITTED_INSTANCE_TYPES):
		print "Permitted values for INSTANCE_TYPE are " + ",".join(PERMITTED_INSTANCE_TYPES) +". You have " + INSTANCE_TYPE
		exit()	
		
def getImageID():
	image_id = ""
	if isRedHat():
		image_id = parser.get("Constants","REDHAT_IMAGE_ID") 
	elif isWindows():
		image_id = parser.get("Constants","WINDOWS_IMAGE_ID") 
	return image_id
	
def getInstallDir():	
	install_dir = ""
	if isRedHat():
		install_dir = parser.get("Constants","REDHAT_INSTALL_DIR") 
	elif isWindows():
		install_dir = parser.get("Constants","WINDOWS_INSTALL_DIR") 
	return install_dir

def getInstallExe():
	exe = ""
	if isRedHat():
		exe = parser.get("Software","MARKLOGIC_REDHAT_EXE") 
	elif isWindows():
		exe = parser.get("Software","MARKLOGIC_WINDOWS_EXE") 
	return exe
	
def getMarkLogicRoot():
	markLogicRootDir = ""
	if isRedHat():
		markLogicRootDir = parser.get("Constants","MARKLOGIC_REDHAT_ROOT") 
	elif isWindows():
		markLogicRootDir = parser.get("Constants","MARKLOGIC_WINDOWS_ROOT") 
	return markLogicRootDir
	
	
MARKLOGIC_DOWNLOAD_URL=parser.get("Software","MARKLOGIC_DOWNLOAD_URL")
PYTHON_EXE=parser.get("Software","PYTHON_EXE")
PYTHON_DOWNLOAD_URL=parser.get("Software","PYTHON_DOWNLOAD_URL")
PYTHON_INSTALL_DIR=parser.get("Software","PYTHON_INSTALL_DIR")
MARKLOGIC_DEVELOPER_LOGIN=parser.get("Software","MARKLOGIC_DEVELOPER_LOGIN")
MARKLOGIC_DEVELOPER_PASS=parser.get("Software","MARKLOGIC_DEVELOPER_PASS")

MARKLOGIC_EXE = getInstallExe()
INSTALL_DIR=getInstallDir()
MARKLOGIC_ROOT = getMarkLogicRoot()

RSA_PRIVATE_KEY=parser.get("Configuration","RSA_PRIVATE_KEY")
HOST_COUNT = int(parser.get("Configuration","HOST_COUNT"))
ADMIN_USER_NAME=parser.get("Configuration","ADMIN_USER_NAME")
ADMIN_PASSWORD=parser.get("Configuration","ADMIN_PASSWORD")
MSTSC_PASSWORD=parser.get("Configuration","MSTSC_PASSWORD")
INSTANCE_SIZE=parser.get("Configuration","INSTANCE_SIZE")
CLUSTER_NAME=parser.get("Configuration","CLUSTER_NAME")
USE_ELASTIC_IP = True if(parser.get("Configuration","USE_ELASTIC_IP").upper() == "TRUE") else  False
DISK_CAPACITY=parser.get("Configuration","DISK_CAPACITY")
EC2_SECURITY_GROUP_NAME=parser.get("Configuration","EC2_SECURITY_GROUP_NAME")
EC2_KEY_PAIR_NAME=parser.get("Configuration","EC2_KEY_PAIR_NAME")

LICENSE_KEY = parser.get("License Details","LICENSE_KEY")
LICENSEE = parser.get("License Details","LICENSEE")
ACCEPTED_AGREEMENT = parser.get("License Details","LICENSE_TYPE")

HOST_FILE = parser.get("Constants","HOST_FILE")
ELASTIC_IP_FILE = parser.get("Constants","ELASTIC_IP_FILE")
EC2_ELASTIC_IP_LIMIT = int(parser.get("Constants","EC2_ELASTIC_IP_LIMIT"))
EBS_DEVICE_NAME=parser.get("Constants","EBS_DEVICE_NAME")
EXPECTED_EBS_DEVICE_NAME=parser.get("Constants","EXPECTED_EBS_DEVICE_NAME")
ACTUAL_EBS_DEVICE_NAME=parser.get("Constants","ACTUAL_EBS_DEVICE_NAME")
MARKLOGIC_REDHAT_DATA_ROOT=parser.get("Constants","MARKLOGIC_REDHAT_DATA_ROOT")

checkOS();


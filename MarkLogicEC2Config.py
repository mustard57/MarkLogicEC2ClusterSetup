import ConfigParser

# Configuration
CONFIG_FILE="config.ini"
                                     									 
parser = ConfigParser.ConfigParser()
parser.read(CONFIG_FILE)

MARKLOGIC_EXE = parser.get("Software","MARKLOGIC_EXE")
MARKLOGIC_DOWNLOAD_URL=parser.get("Software","MARKLOGIC_DOWNLOAD_URL")
MARKLOGIC_ROOT = parser.get("Software","MARKLOGIC_INSTALL_DIR")								 

PYTHON_DOWNLOAD_URL=parser.get("Software","PYTHON_DOWNLOAD_URL")
PYTHON_EXE=parser.get("Software","PYTHON_EXE")
PYTHON_INSTALL_DIR=parser.get("Software","PYTHON_INSTALL_DIR")
INSTALL_DIR=parser.get("Configuration","INSTALL_DIR")
RSA_PRIVATE_KEY=parser.get("Configuration","RSA_PRIVATE_KEY")

HOST_FILE = parser.get("Constants","HOST_FILE")
HOST_COUNT = int(parser.get("Configuration","HOST_COUNT"))

ELASTIC_IP_FILE = parser.get("Constants","ELASTIC_IP_FILE")
ADMIN_USER_NAME=parser.get("Configuration","ADMIN_USER_NAME")
ADMIN_PASSWORD=parser.get("Configuration","ADMIN_PASSWORD")
MSTSC_PASSWORD=parser.get("Configuration","MSTSC_PASSWORD")

CLUSTER_NAME=parser.get("Configuration","CLUSTER_NAME")

LICENSE_KEY = parser.get("License Details","LICENSE_KEY")
LICENSEE = parser.get("License Details","LICENSEE")
ACCEPTED_AGREEMENT = parser.get("License Details","LICENSE_TYPE")

USE_ELASTIC_IP = True if(parser.get("Configuration","USE_ELASTIC_IP").upper() == "TRUE") else  False
EC2_ELASTIC_IP_LIMIT = int(parser.get("Constants","EC2_ELASTIC_IP_LIMIT"))

# Constants
HTML_DIR="html"
MSTSC_DIR="mstsc"
POWERSHELL_DIR = "pws"
SESSION_DIR = "sessions"



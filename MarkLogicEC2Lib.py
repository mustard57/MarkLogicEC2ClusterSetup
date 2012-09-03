import os
import sys
import time
import urllib
import urllib2
from MarkLogicEC2Config import ADMIN_USER_NAME,ADMIN_PASSWORD,POWERSHELL_DIR,HTML_DIR,MSTSC_DIR,SESSION_DIR

EC2_RESOLUTION_URL = "http://169.254.169.254/2009-04-04/meta-data/public-hostname"

def sys(message, cmd):
	print(message)
	os.system(cmd)
	time.sleep(10)
	
def httpProcess(message, url, args = "", debug = False):
	print message
	request = urllib2.Request(url)
	if args == "":
		response = urllib2.urlopen(request)
	else:
		response = urllib2.urlopen(request, urllib.urlencode(args))
	if (debug == True):
		data = response.read()
		print data
		
def configureAuthHttpProcess(host):
	href = "http://"+host+":8001"
	print "Configuring auth for " + href
	passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
	passman.add_password(None, href, ADMIN_USER_NAME, ADMIN_PASSWORD)
	authhandler = urllib2.HTTPDigestAuthHandler(passman)
	opener = urllib2.build_opener(authhandler)
	urllib2.install_opener(opener)		

def getEC2Name():
	request = urllib2.Request(EC2_RESOLUTION_URL)
	response = urllib2.urlopen(request)	
	data = response.read().decode()	
	return data

def clearDirectory(dirName):
	if os.path.isdir(dirName):
		for file in os.listdir(dirName):
			os.remove(dirName + "/" + file)

def removeDirectory(dirName):
	if os.path.isdir(dirName):
		os.rmdir(dirName)
			
def checkDirectory(dirName):
	if not os.path.isdir(dirName):
		os.makedirs(dirName)

def checkDirectories():
	checkDirectory(POWERSHELL_DIR)
	checkDirectory(HTML_DIR)
	checkDirectory(MSTSC_DIR)
	checkDirectory(SESSION_DIR)

def clearDirectories():
	clearDirectory(POWERSHELL_DIR)
	clearDirectory(HTML_DIR)
	clearDirectory(MSTSC_DIR)
	clearDirectory(SESSION_DIR)

def removeDirectories():
	removeDirectory(POWERSHELL_DIR)
	removeDirectory(HTML_DIR)
	removeDirectory(MSTSC_DIR)
	removeDirectory(SESSION_DIR)
	
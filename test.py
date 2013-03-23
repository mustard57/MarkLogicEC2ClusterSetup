import MarkLogicEC2Lib
import MarkLogicEC2Config
import sys
import boto
import time
import os
import glob
import rsa
import re

SLEEP_PERIOD = 30
ec2 = boto.connect_ec2()

def getInstances():
	instances = []
	for i in ec2.get_all_instances():
		instances.append(str(i.instances[0].id))
	return instances

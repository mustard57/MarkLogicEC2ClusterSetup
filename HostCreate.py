import boto
import time
import MarkLogicEC2Config

# Command to enable powershell on remote host
cmd = '<powershell>Enable-PSRemoting -Force</powershell>'
SLEEP_PERIOD=15

# Connext to EC2
ec2 = boto.connect_ec2()
f = open(MarkLogicEC2Config.HOST_FILE,"w")

# Create Hosts
for i in range(0,MarkLogicEC2Config.HOST_COUNT):
		
	reservation = ec2.run_instances(image_id='ami-71b50018',instance_type="t1.micro",key_name="HP",security_groups=["MarkLogic"],user_data=cmd)
	instance = ec2.get_all_instances()[-1].instances[0]
	print instance.id
	
	# Check we are in the running state
	while True:		
		instance = ec2.get_all_instances()[-1].instances[0]
		if instance.state <> "running":
			print "Instance not yet in running state"
		else:
			break
		time.sleep(SLEEP_PERIOD)
	
	if (MarkLogicEC2Config.USE_ELASTIC_IP):
		if(len(ec2.get_all_addresses()) >= MarkLogicEC2Config.EC2_ELASTIC_IP_LIMIT):
			print "You've used "+str(MarkLogicEC2Config.EC2_ELASTIC_IP_LIMIT)+" elastic IP addresses which is the limit. Configuring without elastic IP"
		else:
			ip = ec2.allocate_address() 	
			ec2.associate_address(instance_id=instance.id,public_ip=ip.public_ip)
			print "Elastic IP "+ip.public_ip+" added"
	else:
		print "Elastic IP use not requested"
		
	print "Host " + instance.id + " created"
	f.write(instance.id+"\n")

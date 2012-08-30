import boto
from MarkLogicEC2Config import HOST_FILE,HOST_COUNT

# Command to enable powershell on remote host
cmd = '<powershell>Enable-PSRemoting -Force</powershell>'

# Connext to EC2
ec2 = boto.connect_ec2()
f = open(HOST_FILE,"w")

# Create Hosts
for i in range(0,HOST_COUNT):
	reservation = ec2.run_instances(image_id='ami-71b50018',instance_type="t1.micro",key_name="HP",security_groups=["MarkLogic"],user_data=cmd)
	instance = ec2.get_all_instances()[-1]
	print "Host " + instance.instances[0].id + " created"
	f.write(instance.instances[0].id+"\n")

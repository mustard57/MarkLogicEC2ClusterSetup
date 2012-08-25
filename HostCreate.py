import boto

cmd = '<powershell>Enable-PSRemoting -Force</powershell>'

ec2 = boto.connect_ec2()

reservation = ec2.run_instances(image_id='ami-71b50018',instance_type="t1.micro",key_name="HP",security_groups=["MarkLogic"],user_data=cmd)

instance = ec2.get_all_instances()[-1]

# print instance.instances[0].public_dns_name
print instance.instances[0].id

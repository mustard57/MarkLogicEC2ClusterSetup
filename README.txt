MarkLogicEC2ClusterSetup
========================

The purpose of this library is to allow the easy setup of MarkLogic clusters on EC2.

Quick Start
===========

Pre-Requisites
==============

Clone this git repository to a local directory  - myDir say, using "git clone https://github.com/mustard57/EC2 myDir"

Make sure you have python 2.6. 2.7 does not work with boto ( see below ) - something to do with unicode. Python 3.0 and above does not work due to substantial syntactical refactoring. 

You will need boto, your interface to EC2. More about it here - http://docs.pythonboto.org. You will find the python install in the lib directory - boto.2.3.0.tar.gz. Do gunzip boto.2.3.0.tar.gz ; tar xvf boto.2.3.0.tar ; cd boto.2.3.0 ; python setup.py to install. You can also download from http://code.google.com/p/boto/downloads/detail?name=boto-2.3.0.tar.gz&can=2&q= . Following install, you should be able to do 'import boto' in python.

Other versions may work, this is the one I used.

You will need rsa, a cryptographic library. I used version 3.1.1. You can find it in the lib directory - rsa-3.1.1.tar.gz. Do gunzip rsa-3.1.1.tar.gz ; tar xvf rsa-3.1.1.tar ; cd rsa-3.1.1 ; python setup.py to install. You can also download from http://pypi.python.org/pypi/rsa. This package is used if creating Windows instances. I recommend you don't - and if so you can comment out the rsa related stuff should you choose.

You need an EC2 account, funded by a credit card.

You need to set up a security group in EC2. This is a system of firewall rules. You're using MarkLogic so make sure ports 7998 - 8002 are open plus any port numbers you use for application servers. If using RedHat, open 22 for ssh. If using windows, open 3389 ( RDP ), 5985 for PowerShell, port 445 to mount remote directories and port 88 for active directory. Give your security group a name. This URL gives you the appropriate editor : https://console.aws.amazon.com/ec2/home?region=us-east-1#s=SecurityGroups

You need to set up a key pair. https://console.aws.amazon.com/ec2/home?region=us-east-1#s=KeyPairs. Your private key should probably be in your ~/.ssh directory.

Finally, in ~/.boto add your Amazon EC2 access keys. You get these from https://portal.aws.amazon.com/gp/aws/securityCredentials#access_credentials

The file format can be seen here under the heading 'Example' http://code.google.com/p/boto/wiki/BotoConfig

If creating Windows instances you will need Windows Powershell on your machine, and you will need to run the refresh and setup commands at least from DOS as administrator.

Configuration
=============

All the config is in config.ini. You need to specify ( in the Configuration section )

RSA_PRIVATE_KEY - the file where your private key is. You only need this if using Windows instances ( not recommended ) for decrypting the Windows password using rsa.
HOST_COUNT - the number of hosts you want in your cluster
ADMIN_USER_NAME - the name of your MarkLogic admin user
ADMIN_PASSWORD - your MarkLogic admin password
CLUSTER_NAME - the name you would like your cluster to be given
USE_ELASTIC_IP - set to TRUE or FALSE. Elastic IPs are permanent IPS which means you can 'save' your cluster. Without them, once you stop your cluster, you will loose all your data.
MSTSC_PASSWORD - set this if you are using Windows. It is the password you will use when logging in using terminal services.
INSTANCE_SIZE - this should be one of t1.micro, m1.small, m1.medium, m1.large, m1.xlarge - this governs how much memory / cpu you have. See http://aws.amazon.com/ec2/instance-types/ for more detail
INSTANCE_TYPE - set to one of RedHat or Windows. This governs your cluster platform
DISK_CAPACITY - if using RedHat, sets the size of the MarkLogic data partition ( in Gb ) 
EC2_SECURITY_GROUP_NAME - the name of your EC2 security group ( see above )
EC2_KEY_PAIR_NAME - the name of your EC2 key pair - see above.

In the license details section,

LICENSE_KEY - the 12 * 4 char ( plus hyphens ) license key you will be using. Note that if you are using clustering you need an Enterprise key.
LICENSEE - the licensee name 
LICENSE_TYPE - if you have a full MarkLogic key use 'development', otherwise 'evaluation' - though this probably will not have enterprise capability.

Quick Start
===========

The following commands are available : thaw|help|freeze|status|cluster|clean|create|setup|refresh|restart|devices|all

They are called by typing 

ec2setup.sh cmd - where cmd is one of the above commands. Use ec2setup.bat if calling from DOS.

In theory, having done the above config you should be able to type

ec2setup.sh all

and an n node cluster will be built for you. In the html sub-directory of myDir you will get a html file that you can click on to take you to the admin console for the host in question.

Single Instance Setup
=====================

To understand the commands in more detail, let's focus on using just one instance.

ec2setup.sh create will create your ec2 node for you.

ec2setup.sh create will create your ec2 node for you, based on INSTANCE_TYPE, INSTANCE_SIZE, EC2_SECURITY_GROUP_NAME and EC2_KEY_PAIR_NAME. If INSTANCE_TYPE=RedHat, a disk volume will be mounted of size DISK_CAPACITY. If USE_ELASTIC_IP is true, you will be assigned a fixed elastic ip.

Here is some sample output

Run mode is create
Created instance i-dc4803a1
Instance not yet in running state
Elastic IP 54.243.182.139 added
Elastic IP added for host i-dc4803a1 - 54.243.182.139
10G disk volume created

Your instance id ( i-dc4803a1 in the above output ) will be written to host_file.txt. If you are using elastic ips that will be written to elastic_ip.txt.

ec2setup.sh status will give you some basic status info e.g.

Run mode is status
Host i-dc4803a1 is in the running state with dns = ec2-54-243-182-139.compute-1.amazonaws.com

You can also use the Amazon console : https://console.aws.amazon.com/ec2

If you want to set up MarkLogic on this host type

ec2setup.sh setup

This will install MarkLogic on your host, using the license credentials above. The security user will be ADMIN_USER_NAME with password ADMIN_PASSWORD. If INSTANCE_TYPE=Windows, your rdp password will be set to MSTSC_PASSWORD. Note that Windows boxes are assigned an initial password by EC2 - but this can take up to half an hour to complete. ec2setup.sh setup will loop until this password is found. It is recommended that 15 min or so are left between create and setup for windows boxes as premature requests for the windows password seem to result in instance unreliability in my experience. Setting MSTSC_PASSWORD requires your ssh private key to descrypt the initial password, hence the specification of RSA_PRIVATE_KEY.

The install will add some xqy files to the Admin directory of your remote host, used for naming the host ( it is given its EC2 dns name ), and setting up clustering.

If using RedHat, your block storage will be mapped, using ln, to the device name /dev/sdf ( specified by EXPECTED_EBS_DEVICE_NAME in config.ini). This is a little workaround required as the EC2 for attaching storage does not use the name you supply! MarkLogic will not start on EC2 without a device on /dev/sdf. Note the setup scripts will format the storage and mount at /var/opt/MarkLogic.

'Local' ( host based ) firewalls ( both Windows and RedHat ) will be turned off.

You will get some useful files following setup. In the html directory, a file with name dns-name.admin.html which when clicked will take you to the admin console. If INSTANCE_TYPE=RedHat, a file called dns-name.ssh.sh will be written to the sessions directory. If run using source <FILENAME> this file will ssh you into the box.

If using windows you get the html file. Also in the mstsc directory a file called dns-name.rdp. In the sessions directory a file called dns-name.session.ps1. If run using powershell -noexit -file <FILENAME> this will 'powershell' you into the host - the Windows equivalent of shell access. In the pws directory you wil see dns-name.resinstall.ps1 which is used for refreshes ( more later ) and downloadmarklogic.ps1 / downloadpython.ps1 / server-setup.ps1 which are scripts used during the setup process.

The windows setup is more complex than the RedHat install. Python 2.6 is native to the RedHat virtual image, but has to be installed for Windows. Also copying / downloading is more difficult. If you look in server-setup.ps1 you can see what's needed.

You can 'freeze' your instance using

ec2setup.sh freeze

This will stop your instance, but will keep your data. The advantage of this is that you do not incur CPU charges, only disk charges. Storage charges are 10c per Gb per month i.e. approx 0.33 cents per day per Gb, or 10 cents per day for 30Gb  - a typical per host charge. The minimum instance charge is 2c per hour or 48c per day ( for the micro instance ) and around 32c per hour or $7.68 per day for large instances. So stopping saves you money. Typical output is

Run mode is freeze
Stopping host i-052baa78
Instance not yet in stopped state
Instance not yet in stopped state
Host stopped

The opposite of freeze is thaw. You can thaw your instance using

ec2setup.sh thaw

This will restart your instance, add your previously defined IPs if USE_ELASTIC_IP = true, 

Run mode is thaw
Starting host i-dc4803a1
Instance not yet in running state
Elastic IP added for host i-dc4803a1 - Address:54.243.182.139
Check device mapping ...
Host started

If using RedHat, your block storage device mapping ( see above ) will be re-mapped using ln. This can sometimes fail  - see below for what to do if this happens.

If running with elastic IPs, or running as a single node, you are good to go following a thaw. However, if you are not using elastic IPs and clustering, your hosts will no longer be able to communicate after a freeze / thaw as the dns names they used to communicate are no longer valid. The bootstrap host will have they other two hosts in the 'disconnected' state.

In this instance you can do a refresh. This re-installs MarkLogic, but does not need to go through the preliminary steps of downloading MarkLogic, copying files across, mapping the block storage. This is particularly relevant when using Windows machines as you do not have to wait will an admin password is assigned. Thawing an instance is faster than creating one also.

To refresh run

ec2setup.sh refresh

Here is some sample output

Run mode is refresh
Refreshing i-dc4803a1
Stopping MarkLogic
Stopping MarkLogic: .[  OK  ]
Remove previous install
Install MarkLogic
Loaded plugins: amazon-id, product-id, rhui-lb, security, subscription-manager
Updating certificate-based repositories.
Unable to read consumer identity
Setting up Install Process
Examining MarkLogic-6.0-1.1.x86_64.rpm: MarkLogic-6.0-1.1.x86_64
MarkLogic-6.0-1.1.x86_64.rpm: does not update installed package.
Error: Nothing to do
Starting MarkLogic: [  OK  ]
Stopping MarkLogic: .[  OK  ]
Starting MarkLogic: [  OK  ]
Configuring auth for http://localhost:8001
2. Installing
3. Starting MarkLogic Instance
4. Configuring licence details
5. Accepting EULA
6. Triggering initial application server config
7a. Restarting Server
7b. Restarting Server
8. Configuring Admin user (security)
9. Testing Admin Connection
Move set host name script
Setting host name
Script completed, visit http://ec2-54-243-182-139.compute-1.amazonaws.com:8001 to access the admin interface.

Finally, you can run the clean command 

ec2setup.sh clean
 
This will terminate your instance and remove any associated elastic ips and block storage. Sample output : 

Run mode is clean
Terminating host i-dc4803a1
Instance not yet in terminated state
Instance not yet in terminated state
Removing volume vol-e155519b
 
Running commands with an argument
=================================

All the above examples show the library working in single instance mode. In fact, the commands thaw,freeze,clean,setup,status,refresh,restart,devices can all take 0 or one arguments. If run without arguments, all hosts listed in host_file.txt, which is populated using the create command, are iterated over. Alternatively you can supply an index e.g.

ec2setup.sh freeze 2

will freeze the second host listed in hosts_file.txt. Or you can supply the id of the host e.g. ec2setup.sh freeze i-dc4803a1.

The create command, if run with an integer e.g.

ec2setup.sh create 5

will create that number of hosts, in this case 5.

Clustering
==========

After you have run something like

ec2setup.sh create 5
ec2setup.sh setup

you can run 'cluster' - which will add all your hosts into a cluster, with the first host created as the bootstrap host. Sample output : 

$ ec2setup.sh cluster
Run mode is cluster
Configuring auth for http://ec2-54-243-185-5.compute-1.amazonaws.com:8001
Configuring auth for http://ec2-54-243-185-6.compute-1.amazonaws.com:8001
Joining Cluster
Configuring auth for http://ec2-54-243-185-7.compute-1.amazonaws.com:8001
Joining Cluster
Configuring auth for http://ec2-54-243-185-5.compute-1.amazonaws.com:8001
Joining Cluster II
Configuring auth for http://ec2-54-243-185-6.compute-1.amazonaws.com:8001
Restarting...
Configuring auth for http://ec2-54-243-185-5.compute-1.amazonaws.com:8001
Joining Cluster II
Configuring auth for http://ec2-54-243-185-7.compute-1.amazonaws.com:8001
Restarting...
Configuring auth for http://ec2-54-243-185-5.compute-1.amazonaws.com:8001
Setting cluster name to Master

Clustering requires two calls for each host - one to add to the cluster and one to write the cluster info back to the original host. Hosts are restarted following addition to a cluster. Finally the cluster is named using CLUSTER_NAME from config.ini
All mode
========

If you run 

ec2setup.sh all

this will create n hosts where n is equal to HOST_COUNT in config.ini. It will then run setup for each host, followed by cluster. The only problem is that at the time setup is called, hosts may not be 'ready' - resulting in errors. By and large, try this, if you get errors, run setup against the hosts that failed, followed by cluster.

Other Commands
==============

We have not yet restart,devices and help.

When thawing a cluster, with elastic ips, in theory you can start using this straight away. In practice, the block storage, where the MarkLogic data assets are kept will have been dismounted and re-mounted, and the elastic ip assigned after host startup, which may leave a running MarkLogic process in an non-usable state. So 

ec2setup.sh restart

is a good idea - which will restart MarkLogic on all your hosts. You can restart a single host using

ec2setup.sh restart index

If for some reason the block storage device mapping has not taken place correctly (signified by a 'bad file number') error then use

ec2setup.sh devices index

to remount the volume for a particular host.

ec2setup.sh help 

gives you a list of commands

Elastic IPs
===========

There is an per user elastic ip limit of five addresses, otherwise it would always make sense to use elastic ips. This is encoded into config.ini as EC2_ELASTIC_IP_LIMIT.

Constants in config.ini
=======================

There are a number of constants in config.ini, which can be changed, but which should probably not be.

HOST_FILE=host_file.txt - the file where host ids are stored
ELASTIC_IP_FILE=elastic_ip.txt - the file where elastic ips are stored
EC2_ELASTIC_IP_LIMIT=5 - the elastic ip limit
WINDOWS_IMAGE_ID=ami-71b50018 - the EC2 image used to create Windows hosts
REDHAT_IMAGE_ID=ami-cc5af9a5 - the EC2 image used to create Red Hat hosts
WINDOWS_INSTALL_DIR=c:\users\administrator\ - the directory where assets are stored during the setup phase, for Windows hosts
REDHAT_INSTALL_DIR=/tmp - the directory where assets are stored during the setup phase, for Red Hat hosts
MARKLOGIC_WINDOWS_ROOT=C:\Program Files\MarkLogic\ - the install directory for MarkLogic on Windows
MARKLOGIC_REDHAT_ROOT=/opt/MarkLogic/ - the install directory for MarkLogic on Red Hat
MARKLOGIC_REDHAT_DATA_ROOT=/var/opt/MarkLogic - the data directory for MarkLogic on Red Hat
EBS_DEVICE_NAME=/dev/sdh - the name given to the additional block storage when creating Red Hat instances. Note EC2 does not actually use this
EXPECTED_EBS_DEVICE_NAME=/dev/sdf - the desired device name of the added block storage
ACTUAL_EBS_DEVICE_NAME=/dev/xvdl - the actual device name of the added block storage - we do ln /dev/xvdl /dev/sdf during setup / thaw to make sure MarkLogic can find the /dev/sdf device

Software section in config.ini
==============================

The versions of MarkLogic are used here, and the download location e.g.

MARKLOGIC_WINDOWS_EXE=MarkLogic-6.0-1.1-amd64.msi
MARKLOGIC_REDHAT_EXE=MarkLogic-6.0-1.1.x86_64.rpm
MARKLOGIC_DOWNLOAD_URL=http://developer.marklogic.com/download/binaries/6.0/
PYTHON_DOWNLOAD_URL=http://www.python.org/ftp/python/2.6/
PYTHON_EXE=python-2.6.amd64.msi
PYTHON_INSTALL_DIR=c:\python26

We also specify the python install location for windows, and it's install location.
























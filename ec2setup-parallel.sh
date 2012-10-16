#!/bin/bash

# Call ec2setup.sh but run multi-threaded
# Use 'jobs' to wait for jobs
# Special mode 'all' runs create,setup,cluster

# Script takes a mode argument
# If there is a second argument, existing logs are not clobbered, otherwise ec2*log deleted every time

MODE=$1
SAVE_LOG=$2

SCRIPT=ec2setup.sh
CONFIG_FILE=config.ini
HOST_COUNT_VARIABLE=HOST_COUNT
# Interval between reports
SLEEP_INTERVAL=5

# Get the number of hosts to iterate over
INSTANCES=`cat $CONFIG_FILE | grep $HOST_COUNT_VARIABLE | perl -ne '@a=(split /\=/,$_) ; print $a[1]'`

# Remove existing log files if no $2
if [ ! $2 ]
then
	for file in `ls ec2*log 2>/dev/null`
	do
		rm $file
	done
fi

if [ $MODE = "remote" ]
then
	echo remote is not an appropriate mode for this script
	exit
fi

if [ $MODE = "help" ]
then
	echo You must run using the bash shell
	$SCRIPT $MODE
	exit
fi

if [ $MODE = "status" ]
then
	$SCRIPT $MODE
	exit
fi

if [ $MODE = "cluster" ]
then
	LOG_FILE=ec2-$MODE.log
	$SCRIPT $MODE > $LOG_FILE
	exit
fi

if [ $MODE = "all" ]
then
	$0 create leave
	$0 setup leave
	$0 cluster leave
	exit
fi

COUNT=0

# Kick jobs off
while [ $COUNT -lt $INSTANCES ]
do
	COUNT=$[$COUNT+1]	
	LOG_FILE=ec2-$MODE-$COUNT.log
	if [ $MODE = "create" ]
	then
		echo Running $SCRIPT $MODE
		$SCRIPT $MODE 2>&1 1>$LOG_FILE &
	else
		echo Running $SCRIPT $MODE $COUNT
		$SCRIPT $MODE $COUNT  2>&1 1>$LOG_FILE &
	fi
	sleep $SLEEP_INTERVAL
done


#Report on jobs
jobcount=$INSTANCES

while [ $jobcount != "0" ]
do
	jobcount=`jobs -r | wc -l`
	echo Remaining $MODE jobs = $jobcount
	sleep $SLEEP_INTERVAL
done

# Clean mode does additional tidy up
if [ $MODE = "clean" ]
then
	echo Tidying up
	$SCRIPT $MODE 
fi

echo Completed $INSTANCES iterations of $MODE mode. See log files ec2-$MODE-* for details

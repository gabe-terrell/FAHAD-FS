# kill runnning python processes
# kill $(ps aux | grep '[p]ython' | awk '{print $2}')
# remove existing files from filesystem -- start with clean directory
# rm -r ./nodefiles/*
# rm ./registrydata/reg.data

INITIAL_NODES=10
NUMBER_ROUNDS=10
MAX_ADDITIONS=5
MAX_UPLOADS=10
MAX_DOWNLOADS=20

MASTER_DIR="./"
MASTER_RUN='master_node.py -p'
MASTER=$MASTER_DIR$MASTER_RUN

FILENODE_DIR="./"
FILENODE_RUN='file_node.py'
FILENODE=$FILENODE_DIR$FILENODE_RUN

CLIENT_DIR='./'
CLIENT_RUN='client.py'
CLIENT=$CLIENT_DIR$CLIENT_RUN

INPUT_DIR='./input/'
OUTPUT_DIR='./output/'

VIEWER_INSTRS='viewer_input.txt'

# start up the master
# NOTE: It's much more helpful to just run master in a seperate window
# printf "Starting master node\n\n"
# python $MASTER > /dev/null &
# sleep 1

##########################################################################

function spawnNodes {
	for _ in `seq 1 $1`;
	do
	    python $FILENODE > /dev/null &
	    sleep 0.5
	done
}

# Determine number of living online filenodes
function nodeCount {
	PIDS="$(ps ax | grep $FILENODE | awk '{print $1}')"
	COUNT=0
	for PID in $PIDS
	do
		((COUNT++))
	done
	echo $((COUNT - 1))
}

# Take all filenodes and randomly decide if each one lives
function nodeRoulette {
	PIDS="$(ps ax | grep $FILENODE | awk '{print $1}')"
	for PID in $PIDS
	do
		CHAMBER=$(($RANDOM % 20))
		if [ "$CHAMBER" -eq "0" ]; then
			echo "RIP $PID"
			kill $PID > /dev/null &
		fi
	done
}

# Create a random file and give it random data
function seedInput {
	FILENAME="$(cat /dev/urandom | env LC_CTYPE=C tr -cd 'a-f0-9' | head -c 32)"
	FILEPATH=$INPUT_DIR$FILENAME
	echo $FILENAME > $FILEPATH

	while [ "$(($RANDOM % 1000))" -gt "0" ]; do
		echo $FILENAME >> $FILEPATH
	done

	echo $FILEPATH
}

# Grab a random file inside of input directory
function randomInput {
	FILES="$(ls $INPUT_DIR)"

	COUNT=0
	for FILE in $FILES
	do
		((COUNT++))
	done

	NUM=$(($RANDOM % $COUNT))
	WINNER=""

	for FILE in $FILES
	do
		((COUNT--))
		if [ "$NUM" -eq "$COUNT" ]; then
			WINNER=$FILE
			break
		fi
	done

	echo $WINNER
}

# Either create a new file or grab an exisiting one
# Waited to use an exisiting file 90% of the time
function randomInputAction {
	if [ "$(($RANDOM % 10))" -eq "0" ];
	then
		echo "$(seedInput)"
	else
		FILE="$(randomInput)"
		echo "$INPUT_DIR$FILE"
	fi
}

function simulate {
	NODE_ADDITIONS="$(($RANDOM % $MAX_ADDITIONS))"
	UPLOADS="$(($RANDOM % $MAX_UPLOADS))"
	DOWNLOADS="$(($RANDOM % $MAX_DOWNLOADS))"

	while :
	do
		sleep 2.0
		CONT=false

		#nodeRoulette > /dev/null &

		if [ "$NODE_ADDITIONS" -gt "0" ]; then
			((NODE_ADDITIONS--))
			CONT=true
			spawnNodes 1
		fi

		if [ "$UPLOADS" -gt "0" ]; then
			((UPLOADS--))
			CONT=true
			python $CLIENT -u $(randomInputAction) / > /dev/null &
		fi

		if [ "$DOWNLOADS" -gt "0" ]; then
			((DOWNLOADS--))
			CONT=true
			python $CLIENT -d /$(randomInput) $OUTPUT_DIR > /dev/null &
		fi

		if [ $CONT = false ]; then
			break
		fi
	done
}

###########################################################################

# test run the viewer
printf "Verifying master by connecting viewer\n\n"
cat $VIEWER_INSTRS | python $CLIENT -v

spawnNodes $INITIAL_NODES

for _ in `seq 1 $NUMBER_ROUNDS`;
do
    simulate
done

# while [ "$(nodeCount)" -gt "1" ]; do
# 	nodeRoulette
# 	sleep 1
# done

#nodeRoulette

# do a couple uploads
# do a couple downloads to check integrity
# run through commands

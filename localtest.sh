# kill runnning python processes
# kill $(ps aux | grep '[p]ython' | awk '{print $2}')
# remove existing files from filesystem -- start with clean directory
# rm -r ./nodefiles/*
# rm ./registrydata/reg.data

INITIAL_NODES=60
INITIAL_FILES=10
NUMBER_ROUNDS=5
MAX_ADDITIONS=10
MAX_UPLOADS=50
MAX_DOWNLOADS=50
TIME_BETWEEN_ACTION=0.1
TIME_BETWEEN_ROUNDS=2.0

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

# Spawn a new filenode (will attempt to use existing directory)
function spawnNodes {
	for _ in `seq 1 $1`;
	do
	    python $FILENODE > /dev/null &
	    sleep 0.5
	done
}

# Spawn a filenode that may attempt to use existing directory or forcively be fresh
function randomSpawnNode {
	FRESH=$(($RANDOM % 2))
	if [ "$FRESH" -eq "0" ];
	then
		python $FILENODE -fresh > /dev/null &
	else
		python $FILENODE > /dev/null &
	fi
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
		CHAMBER=$(($RANDOM % 50))
		if [ "$CHAMBER" -eq "0" ]; then
			echo "RIP $PID"
			kill $PID &> /dev/null &
		fi
	done
}

# Create a random file and give it random data
function seedInput {
	SEED_AMOUNT="$(($RANDOM % 1000))"
	SEED_NAME="seed$(($SEED_AMOUNT * 32 + 1))"
	SEED_DATA="$(cat /dev/urandom | env LC_CTYPE=C tr -cd 'a-f0-9' | head -c 32)"
	FILEPATH=$INPUT_DIR$SEED_NAME
	echo $SEE > $FILEPATH

	while [ "$SEED_AMOUNT" -gt "0" ]; do
		printf "$SEED_DATA" >> $FILEPATH
		((SEED_AMOUNT--))
	done

	echo $FILEPATH
}

function numInputFiles {
	FILES="$(ls $INPUT_DIR)"

	COUNT=0
	for FILE in $FILES
	do
		((COUNT++))
	done

	echo $COUNT
}

# Grab a random file inside of input directory
function randomInput {
	FILES="$(ls $INPUT_DIR)"

	COUNT="$(numInputFiles)"

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
# Weighted to use an exisiting file 90% of the time
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

	echo "$NODE_ADDITIONS new filenodes"
	echo "$UPLOADS file uploads"
	printf "$DOWNLOADS file downloads\n\n"

	while :
	do
		sleep $TIME_BETWEEN_ROUNDS
		CONT=false

		nodeRoulette &> /dev/null &

		if [ "$NODE_ADDITIONS" -gt "0" ]; then
			((NODE_ADDITIONS--))
			CONT=true
			randomSpawnNode
			sleep $TIME_BETWEEN_ACTION
		fi

		if [ "$UPLOADS" -gt "0" ]; then
			((UPLOADS--))
			CONT=true
			python $CLIENT -u $(randomInputAction) / &> /dev/null &
			sleep $TIME_BETWEEN_ACTION
		fi

		if [ "$DOWNLOADS" -gt "0" ]; then
			((DOWNLOADS--))
			CONT=true
			python $CLIENT -d /$(randomInput) $OUTPUT_DIR &> /dev/null &
			sleep $TIME_BETWEEN_ACTION
		fi

		if [ $CONT = false ]; then
			break
		fi
	done
}

###########################################################################

# Create directories if they don't already exist
mkdir -p $INPUT_DIR
mkdir -p $OUTPUT_DIR

# Seed input if not enough already
while [ "$(numInputFiles)" -lt "$INITIAL_FILES" ]; do
	seedInput &> /dev/null &
done

# Connect a client instance to verify master server running
printf "Verifying master by connecting viewer\n\n"
cat $VIEWER_INSTRS | python $CLIENT -v

# Spawn initial batch of nodes
spawnNodes $INITIAL_NODES

# Run n simulations
for ROUND in `seq 1 $NUMBER_ROUNDS`;
do
	echo "Simulating round $ROUND"
    simulate
done

printf "End of simulation. Running viewer instance.\n\n"
cat $VIEWER_INSTRS | python $CLIENT -v

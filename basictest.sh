#1. open file viewer, see that only root exists, maybe make some directories
#2. wake up some nodes, upload some files to them, verify with the viewer
#3. delete files, verify with viewer
#4. show test of concurrent client getting blocked by session
#5. use stat just to show
#6. start doing a bunch of nodes
#7. upload files to nodes, show simple replication for underreplicated files when we delete nodes
#8. show that the nodes that have less stored will get priority in receiving new data
#9. show still alive pings

./setup.sh

rm -r ./nodefiles/*
rm ./registrydata/reg.data

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

mkdir -p $INPUT_DIR
mkdir -p $OUTPUT_DIR

rm $INPUT_DIR*
rm $OUTPUT_DIR*

#1. open file viewer, see that only root exists, maybe make some directories
printf "Verifying working master by connecting client file viewer\n\n"
printf "ls\nmkdir docs\ncd docs\npwd\ncd ..\nls\nexit\n" | python client.py -v
printf "\n\n\n"

read -p ""

#2. wake up some nodes, upload some files to them, verify with the viewer

# wake up nodes
NUM_INITIAL_NODES=9
echo "Connecting $NUM_INITIAL_NODES file nodes to the system"

function spawnNodes {
	for _ in `seq 1 $1`;
	do
	    python $FILENODE > /dev/null &
	    sleep 0.5
	done

}

spawnNodes $NUM_INITIAL_NODES

read -p ""

# create some files
function seedInput {
	SEED_AMOUNT="$(($RANDOM % 1000))"
	SEED_NAME="seed$(($SEED_AMOUNT * 32 + 1))"
	SEED_DATA="$(cat /dev/urandom | env LC_CTYPE=C tr -cd 'a-f0-9' | head -c 32)"
	FILEPATH=$INPUT_DIR$SEED_NAME

	while [ "$SEED_AMOUNT" -gt "0" ]; do
		printf "$SEED_DATA" >> $FILEPATH
		((SEED_AMOUNT--))
	done

	echo $SEED_NAME
}

FIRST_FILE="$(seedInput)"
SECOND_FILE="$(seedInput)"
THIRD_FILE="$(seedInput)"

printf "\n\nCreating three files to upload to server:\n"
printf "\t$FIRST_FILE\n"
printf "\t$SECOND_FILE\n"
printf "\t$THIRD_FILE\n\n"

# upload files
echo "Uploading files concurrently"

python $CLIENT -u $INPUT_DIR$FIRST_FILE / &> /dev/null &
sleep 0.5
python $CLIENT -u $INPUT_DIR$SECOND_FILE / &> /dev/null &
sleep 0.5
python $CLIENT -u $INPUT_DIR$THIRD_FILE / &> /dev/null &
sleep 1.5

printf "\nVerifying receipt of files using viewer\n"
printf "ls\nexit\n" | python $CLIENT -v

read -p ""

#3. delete files, verify
printf "\n\n\nDeleting $THIRD_FILE\n"
python $CLIENT --rm /$THIRD_FILE

echo "Verifying delete by requesting to download deleted file"
python $CLIENT -d /$THIRD_FILE .
printf "\n\n\n"

read -p ""

#4. show test of concurrent client getting blocked by session
#5. use stat just to show
#??????

#6. start doing a bunch of nodes
# NUM_NEW_NODES=3
# echo "Connecting $NUM_NEW_NODES additional nodes to the system"
# spawnNodes $NUM_NEW_NODES
# sleep 5.0
# printf "\n\n\n"

#7. Show simple replication for underreplicated files when we delete nodes
function snipeNode {
	PIDS="$(ps ax | grep $FILENODE | awk '{print $1}')"
	for PID in $PIDS
	do
		kill $PID &> /dev/null &
		break
	done
}

echo "Testing node resiliency by killing first two nodes in system"
snipeNode
sleep 0.2
snipeNode

read -p ""
echo "Testing node resiliency by killing two more nodes"
snipeNode
sleep 0.2
snipeNode
sleep 0.2
#snipeNode
sleep 0.2

read -p ""
printf "\n\nConfirming file resiliency by downloading files\n"
python $CLIENT -d /$FIRST_FILE $OUTPUT_DIR
sleep 1.0
python $CLIENT -d /$SECOND_FILE $OUTPUT_DIR
sleep 1.0

echo "Listing files in output directory"
ls $OUTPUT_DIR

#8. show that the nodes that have less stored will get priority in receiving new data
#9. show still alive pings

## This is acomplished within master
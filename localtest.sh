# bleh doesn't work
# kill runnning python processes
kill $(ps aux | grep '[p]ython' | awk '{print $2}')
# remove existing files from filesystem -- start with clean directory
rm -r ./nodefiles/*

$MASTER_DIR = "./"
$MASTER_RUN = 'master_node.py'
$FILENODE_DIR = "./"
$FILENODE_RUN = 'file_node.py'
# run master and several file nodes
python $MASTER_RUN &

for i in `seq 1 3`;
do
        python $FILENODE_DIR$FILENODE_RUN &
done

# do a couple uploads
# do a couple downloads to check integrity
# run through commands

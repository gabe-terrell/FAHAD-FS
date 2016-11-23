Distributed File System
=======================

A distributed file system written in Python.

Three main components:
- __Master Node__: Tracks and organizes files across a network of File Nodes; directs clients to Filenodes.
- __File Node__: Stores files on local storage within the file node host machine. Receives and serves files from/to clients.
- __Client__: communicates with Master Node and File Nodes

#### Usage:

1. Start the Master Node:
    - ```$ python master_node.py```
2. Start a File Node:
    - ```$ python file_node.py``` (single node on one host machine)
    - ```$ python file_node.py -test``` (multiple file nodes on one host machine)
3. Run a client:
    - ```$ python client.py -v``` (open the filesystem viewer)
    - ```$ python client.py -d [PATH_ON_SERVER] [LOCAL_PATH]``` (download file from filesystem to client machine)
    - ```$ python client.py -u [PATH_ON_SERVER] [LOCAL_PATH]``` (upload file from client machine to filesystem)


#### TODO:

- [X] Client-side file viewer
- [X] File node ID querying
- [X] File storage on file nodes
- [X] *File upload through master node* (to-be-deprecated)
- [ ] *File download through master node* (not to be implemented)
- [X] Support for simultaenous clients (multithreaded master node and file nodes)
- [X] Multiple filenodes on same host machine
    - Helpful for testing, unlikely in "production"
- [ ] __File download direct from client to filenode__-- high priority
- [ ] __File upload direct from filenode to client__-- high priority
- [ ] File replication across multiple file nodes
    - file nodes will redistribute files to fresh node upon entry to the network (directed by master)
    - files that are under-replicated (under k = 3) due to node failure will be copied to new machines

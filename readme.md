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
    - ```$ python file_node.py```
3. Run a client:
    - ```$ python client.py -v``` (open the filesystem viewer)
    - ```$ python client.py -d [PATH_ON_SERVER] [LOCAL_PATH]``` (download file from filesystem to client machine)
    - ```$ python client.py -u [PATH_ON_SERVER] [LOCAL_PATH]``` (upload file from client machine to filesystem)


#### TODO:

- [X] Client-side file viewer
- [X] File node wakeup registration
    - [X] Filenode ID querying
    - [X] Filenode dynamic server address registration
- [X] File storage on file nodes
- [X] *File upload through master node* (to-be-deprecated)
- [ ] *File download through master node* (not to be implemented)
- [X] Support for simultaenous clients (multithreaded master node and file nodes)
- [X] Multiple filenodes on same host machine
    - Helpful for testing, unlikely in "production"
- [ ] __File upload direct from client to filenode__-- high priority
    - [X] server handshake with location passing
    - [X] transmission from client to filenode and storage on filenode local filesystem
    - [ ] 3-way transmission integrity check between filenode, master, client
- [ ] __File download direct from filenode to client__-- high priority
    - [ ] server handshake with location passing
    - [ ] transmission from filenode to client
    - [ ] 3-way transmission integrity check between filenode, master, client
- [ ] File replication across multiple file nodes
    - [ ] load balancing for selection of file nodes to receive data
    - [ ] file nodes will redistribute files to fresh node upon entry to the network (directed by master)
    - [ ] files that are under-replicated (under k = 3) due to node failure will be copied to new machines

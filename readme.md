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



#### TODO:

- [X] File node ID querying
- [ ] File download direct from client to filenode
- [ ] File upload direct from filenode to masternode
- [X] File upload through master node
- [ ] File download through master node
- [X] Multiple filenodes on same host machine
    - Helpful for testing, unlikely in "production"
- [ ] File replication across multiple file nodes

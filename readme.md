Distributed File System
=======================

A distributed file system written in Python.

Three main components:
- __Master Node__: Tracks and organizes files across a network of File Nodes; directs clients to Filenodes.
- __File Node__: Stores files on local storage within the file node host machine. Receives and serves files from/to clients.
- __Client__: communicates with Master Node and File Nodes

![alt text](https://drive.google.com/open?id=0BwBokiOl5S3hVmVaUkRmQ0tHWGs "Architecture Overview")

#### Usage:

1. Start the Master Node:
    - ```$ python master_node.py```
2. Start a File Node:
- Single file node on one machine:
    - ```$ python file_node.py```
- Multiple file nodes on one machine (unpredictable server addresses):
    - ```$ python file_node.py -test```



#### TODO:

- [X] File node ID querying
- [ ] File download direct from client to filenode
- [ ] File upload direct from filenode to masternode
- [X] File upload through master node
- [ ] File download through master node
- [X] Multiple filenodes on same host machine
    - Helpful for testing, unlikely in "production"
- [ ] File replication across multiple file nodes

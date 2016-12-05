Distributed File System
=======================

A distributed file system written in Python.

Three main components:
- __Master Node__: Tracks and organizes files across a network of File Nodes; directs clients to Filenodes.
- __File Node(s)__: Store files on local storage within the file node host machine. Receives and serves files from/to clients.
- __Client__: communicates with Master Node and File Nodes

#### Usage:

1. Start the Master Node:
    1. ```$ ./cleanup.sh```
    2. ```$ python master_node.py```
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
- [X] Support for simultaneous clients (multithreaded master node and file nodes)
    - [X] Multiple client access to filesystem
    - [ ] Safe concurrent accessing (to avoid simultaneous accesses on the same resource)
- [X] Multiple filenodes on same host machine (Helpful for testing, unlikely in "production")
- [X] Miscellaneous filesystem operations:
    - [X] STAT: ```python client.py --stat 'path_on_server'```
    - [X] CP: ...
    - [ ] MKDIR: ...
    - [ ] RMDIR: ...
    - [ ] MV: ...
    - [ ] RM: ...
- [ ] __File upload direct from client to filenode__
    - [X] server handshake with location passing
    - [X] transmission from client to filenode and storage on filenode local filesystem
    - [X] 3-way transmission integrity check between filenode, master, client
- [ ] __File download direct from filenode to client__-- high priority
    - [ ] server handshake with location passing
    - [ ] transmission from filenode to client
    - [ ] 3-way transmission integrity check between filenode, master, client
- [X] File replication across multiple file nodes
    - [X] filesystem mirrors all files across all active nodes
    - [ ] load balancing for selection of file nodes to receive data
        - load balancing for size: each file node has an equal amount of data
        - load balancing to manage bandwidth to each node: keep filenodes from getting choked
    - [ ] redistribution of files to fresh nodes upon entry to the network (directed by master)
    - [ ] re-replication of files to new nodes under occurrence of file node failure
- [ ] File Node sends 'still-alive' pings to master so master can track 'active' nodes
- [ ] Client: splitting of large files across multiple file nodes
- [ ] Client: caching of recently accessed files at host machine
    - Set TTL to determine how long file can be cached
    - update of cached file spurs new update of file on network

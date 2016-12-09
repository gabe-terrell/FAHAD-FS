#### __FAHADFS__ (Failure Averse Highly Available Distributed File System)


A distributed file system written in Python.

Three main components:
- __Master Node__: Tracks and organizes files across a network of File Nodes; directs clients to Filenodes.
- __File Node(s)__: Store files on local storage within the file node host machine. Receives and serves files from/to clients.
- __Client__: communicates with Master Node and File Nodes

#### Usage:

0. For the first time...
    - ```$ ./setup.sh$``` (will remove filesystem data if run after saving data to filesystem)
1. Start the Master Node:
    1. ```$ ./cleanup.sh [-n -m]``` (-n removes preexising data stored on filenodes, -m removes preexisting records of data from masternode)
    2. Run from file or with a fresh filesystem:
        - ```$ python master_node.py``` (uses default file for initialization)
        - ```$ python master_node.py --fresh-as-a-daisy```
2. Start a File Node:
    - ```$ python file_node.py```
3. Run a client:
    - ```$ python client.py -v``` (open the filesystem viewer)
    - ```$ python client.py -d [PATH_ON_SERVER] [LOCAL_PATH]``` (download file from filesystem to client machine)
    - ```$ python client.py -u [PATH_ON_SERVER] [LOCAL_PATH]``` (upload file from client machine to filesystem)
    - ```python client.py --stat [PATH_ON_SERVER]``` (get info on a file)
    - ```python client.py --mkdir [PATH_ON_SERVER]``` (make a directory)
    - ```python client.py --rm [PATH_ON_SERVER]``` (remove a file)


#### TODO:

- [X] Client-side file viewer
- [X] File node wakeup registration
    - [X] Filenode ID querying
    - [X] Filenode dynamic server address registration
- [X] File storage on file nodes
- [X] Support for simultaneous clients (multithreaded master node and file nodes)
    - [X] Multiple client access to filesystem
    - [X] Safe concurrent accessing (to avoid simultaneous accesses on the same resource)
        - uses "session-based" architecture to open a "session" with a particular file such that a second client cannot access a file while it is already "in session"
- [X] Multiple filenodes on same host machine (Helpful for testing, unlikely in "production")
- [X] Miscellaneous filesystem operations:
    - [X] STAT: ```python client.py --stat <path_on_server>```
    - [X] MKDIR: ```python client.py --mkdir <path_on_server>```
    - [X] RM: ```python client.py --rm <path_on_server>```
    - [ ] CP: unimplemented
    - [ ] RMDIR: unimplemented
    - [ ] MV: unimplemented
- [X] __File upload direct from client to filenode__
    - [X] server handshake with location passing
    - [X] transmission from client to filenode and storage on filenode local filesystem
    - [X] 3-way transmission integrity check between filenode, master, client
- [X] __File download direct from filenode to client__
    - [X] server handshake with location passing
    - [X] transmission from filenode to client
    - [X] 3-way transmission integrity check between filenode, master, client
- [X] File replication across multiple file nodes
    - [X] filesystem replicates files using replication factor (k = 3)

- [X] load balancing for selection of file nodes to receive data
    - [X] load balancing for size: file nodes with minimum data receive priority
    - [X] load balancing to manage bandwidth to each node: keep filenodes from getting choked
- [X] Dynamic file redistribution
    - [ ] Redistribution of files to fresh nodes upon entry to the network (directed by master)
    - [X] Replication of files to new nodes under occurrence of file node failure
- [X] File Node sends 'still-alive' pings to master so master can track 'active' nodes
- [ ] Client: splitting of large files across multiple file nodes in 'chunks'
- [ ] Client: caching of recently accessed files at host machine
    - Set TTL to determine how long file can be cached
    - Update of cached file spurs new update of file on network

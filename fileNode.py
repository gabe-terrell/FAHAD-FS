# file node for distributed file system

import os
import sys
import time
import socket
import pickle
import threading
from threadedServer import threadedServer

class FileNode:

    ### TODO: threaded nodeserver
    def __init__(self, masterAddr, serverPort = 90000):

        self.masterAddr = masterAddr
        self.port       = serverPort
        self.nodeID     = self.getNodeID()
        self.dir        = self.openDir()
        self.server     = NodeServer(self.port)

    def getNodeID(self):

        nodeID = 1
        print "Node ID: ", int(nodeID)
        return nodeID
        # TODO
        # 1. client-connect to master node
        # 2.send master node list of directories i have access to
        # 3. master node will reply with the directory i should use

    def openDir(self):

        if self.nodeID is None:
            print "Opening filenode subsystem before nodeID is set."
            sys.exit()
        else:
            filename = "nodedump" + str(self.nodeID) + ".dir"

        if os.path.isfile(filename):
            self.dirfile = open(filename, "rwb+")
            self.dir = pickle.load(self.dirfile)
        else:
            self.dirfile = open(filename, "w+")
            self.dir     = {}
            pickle.dump(self.dir, self.dirfile)

        print "Current node contents: ", self.dir

    def saveState(self):
        print "Saving filesystem chunk state to disk..."
        pickle.dump(self.dir, self.dirfile)
        print "FS saved to disk."

    def runServer(self):
        self.server.listen()


class NodeServer(threadedServer):

    def __init__(self, port):

        self.host = socket.gethostbyname('')
        self.port = port
        self.timeout = 60 # seconds
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def listen(self):

        self.sock.listen(5)
        while True:
            print "File node waiting for connections from the mothership..."
            clisock, cliAddr = self.sock.accept()
            clisock.settimeout(self.timeout)

            cliThread = threading.Thread( target = self.listenToClient,
                                          args   = (clisock,cliAddr))
            cliThread.start()



    def listenToClient(self, clisock, cliAddr):

        BUFSIZE = 1024
        while True:
            try:
                data = clisock.recv(BUFSIZE)
                if data:
                    response = data
                    clisock.send(response)
                else:
                    raise error("Client disconnected")
            except:
                clisock.close()



def usage_error():
    print "Usage: python fileNode.py <PORTNUM> <MASTER_IP>"
    sys.exit()

def main(argv):

    try:
        portnum     = int(sys.argv[1])
        masterAddr  = sys.argv[2]
    except:
        usage_error()

    fnode = FileNode(masterAddr, serverPort = portnum)
    fnode.runServer()

if __name__ == '__main__':
    main(sys.argv)

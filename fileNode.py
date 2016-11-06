# file node for distributed file system

import os
import sys
import time
import socket
import pickle
import threading

class FileNode:

    def __init__(self, masterAddr, serverPort = 90000):

        self.masterAddr = masterAddr
        self.port       = serverPort
        self.nodeID     = None
        self.server     = None
        self.dir        = None

    def assignNodeID(self):

        self.nodeID = 1
        print "Node ID: ", int(self.nodeID)
        # connect to master node
        # send master node list of directories i have access to
        # master node will reply with the directory i should use

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


    def runServer(self):
        self.server = Server(self.port)
        self.server.listen()

class Server():

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
            threading.Thread(target = self.listenToClient,
                             args   = (clisock,cliAddr)).start()



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
    fnode.assignNodeID()
    fnode.openDir()
    fnode.runServer()

if __name__ == '__main__':
    main(sys.argv)

# file node for distributed file system

import os
import sys
import time
import socket
import pickle
import setup
import threading
import json
from threaded_server import ThreadedServer

NODE_FILEPATH = "./nodefiles/"
NODESERVER_ADDR, NODESERVER_PORT  = setup.FILE_NODE_ADDR


class FileNode:

    def __init__(self, masterAddr = NODESERVER_ADDR, serverPort = NODESERVER_PORT):

        self.masterAddr = masterAddr
        self.port       = serverPort
        self.nodeID     = self.getNodeID()
        self.dir        = self.openDir()
        self.server     = ThreadedServer(serverPort)

    def getNodeID(self):

        dirs = os.listdir(NODE_FILEPATH)
        request = json.dumps(dirs)
        print "Starting file node"
        print "List of eligible directories: " + request
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            print "Attempting connection to " + str(setup.MASTER_NODE_ADDR)
            clientsocket.connect((localhost, 9090))
            clientsocket.send(request)
            response = clientsocket.recv(setup.BUFSIZE)
            # TODO: echo contents of directory back to server to affirm
            # correct contents. Could echo checksums to confirm data integrity
            print "Starting file node on directory dump: " + response
        except:
            print "Unable to connect to master node."
            # sys.exit()


        clientsocket.close()
        nodeID = 1
        return nodeID

    def openDir(self):

        if self.nodeID is None:
            print "Opening filenode subsystem before nodeID is set."
            sys.exit()
        else:
            filename = NODE_FILEPATH + "nodedump" + str(self.nodeID) + ".dir"

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


def usage_error():
    print "Usage: python fileNode.py <PORTNUM> <MASTER_IP>"
    sys.exit()

def main(argv):

    fnode = FileNode()
    fnode.runServer()

if __name__ == '__main__':
    main(sys.argv)

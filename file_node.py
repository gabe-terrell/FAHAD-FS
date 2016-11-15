# file node for distributed file system

import os
import re
import sys
import time
import socket
import pickle
import setup
import threading
import json
from filenode_master_protocol import *
from threaded_server import ThreadedServer

NODE_FILEPATH = "./nodefiles/"
NODESERVER_ADDR, NODESERVER_PORT  = setup.FILE_NODE_ADDR


class FileNode:

    def __init__(self, masterAddr = NODESERVER_ADDR, serverPort = NODESERVER_PORT):

        self.masterAddr = masterAddr
        self.port       = serverPort
        self.nodeID     = self.getNodeID()
        self.dir        = self.openDir()
        self.server     = ThreadedServer(setup.FILE_NODE_ADDR)

    def getNodeID(self):

        dirs = os.listdir(NODE_FILEPATH)
        # uses regex to pull integers out of directory filenames
        ids = [int(re.findall('\d+', d).pop()) for d in dirs]
        request = NodeRequest(NodeRequestType.idquery, ids).toJson()
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:

            clientsocket.connect(setup.MASTER_NODE_ADDR)
            clientsocket.send(request)
            print "ID REQUEST: " + request
            response = clientsocket.recv(setup.BUFSIZE)
            print "ID RESPONSE: " + response
            response = json.loads(response)

            if not 'type' in response:
                raise error("Master sent bad response.")

            if response["type"] is MasterResponseType.nodeid:
                nodeID = int(response['data'])

            # TODO: echo contents of directory back to server to affirm
            # correct contents. Could echo checksums to confirm data integrity

        except Exception, ex:

            print "Unable to obtain filenode ID becuase exception \n" + \
            str(ex) + "\n" + " was raised. Shutting down."
            sys.exit()

        clientsocket.close()
        print "Filenode has ID: " + str(nodeID)
        return nodeID

    def openDir(self):

        if self.nodeID is None:
            print "Opening filenode subsystem before nodeID is set."
            sys.exit()
        else:
            filename = NODE_FILEPATH + "nodedump" + str(self.nodeID) + ".data"

        if os.path.isfile(filename):
            self.dirfile = open(filename, "rwb+")
            self.dir = pickle.load(self.dirfile)

        else:
            self.dirfile = open(filename, "w+")
            self.dir     = {} # fresh local filesystem

        self.saveState()
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

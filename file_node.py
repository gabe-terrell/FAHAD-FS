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
from subprocess import call
from filenode_master_protocol import *
from threaded_server import ThreadedServer

NODE_FILEPATH = "./nodefiles/"
NODESERVER_ADDR, NODESERVER_PORT  = setup.FILE_NODE_ADDR


class FileNode:

    def __init__(self, masterAddr = NODESERVER_ADDR, serverPort = NODESERVER_PORT, mode = None):

        self.masterAddr = masterAddr
        self.port       = serverPort
        self.nodeID     = self.getNodeID()
        self.dir        = self.openDir()
        self.server     = ThreadedServer(setup.FILE_NODE_ADDR, mode)


    def start(self):

        target = self.__startServer
        self.server.handler = self.handleConnection
        serverThread = Thread(target=target, args=[self.server])
        serverThread.start()


    def __startServer(self, server):
        server.listen()


    def getNodeID(self):

        dirs = os.listdir(NODE_FILEPATH)
        ids = [int(re.findall('\d+', d).pop()) for d in dirs]
        request = NodeRequest(NodeRequestType.idquery, ids).toJson()
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:

            clientsocket.connect(setup.MASTER_NODE_ADDR)
            clientsocket.send(request)
            print "ID REQUEST: " + request
            response = clientsocket.recv(setup.BUFSIZE)
            response = json.loads(response)

            if not 'type' in response:
                raise error("Master sent bad response.")

            if response['type'] is MasterResponseType.nodeid:
                nodeID = int(response['data'])

            elif response['type'] is MasterResponseType.shutdown:
                print "Recieved shutdown signal from masternode."
                sys.exit()

            else:
                print "Recieved invalid response type from masternode."
                sys.exit()

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

        self.dirfile = filename

        if os.path.isfile(filename):

            try:
                file = open(self.dirfile, 'rwb+')
                self.dir = pickle.load(file)
                file.close()
            except Exception as ex:
                errorfile = NODE_FILEPATH + "nodedump" + str(self.nodeID) + "_CORRUPT.data"
                os.system(("mv " + filename + " " + errorfile))
                print "Error when loading preexisting file chunk."
                print "Please repair " + errorfile + " to resolve error."
                print "Initializing new filesystem chunk at " + filename
                self.dir = {}

        else:
            self.dir     = {}

        self.saveState()
        print "Current node contents: " + str(self.dir)

    def saveState(self):
        print "Saving filesystem chunk state to disk..."
        file = open(self.dirfile, 'w+')
        pickle.dump(self.dir, file)
        file.close()
        print "FS saved to disk."

    def start(self):
        self.server.listen()

    def handleConnection(self, socket, address):

        # TODO: error checking and partial reads

        while True:

            try:
                data = socket.recv(setup.BUFSIZE)

                if not data: raise error("No data received from client.")
                if not 'type' in request:
                    raise error("Filenode sent bad request.")

                request = json.loads(data)
                type = request['type']

                if type is MasterRequestType.store:
                    self.dir[request['key']] = request['data']
                    print self.dir[request['key']]

                elif type is MasterRequestType.retrieve:
                    data = self.dir[request['key']]
                    response = MasterResponse(NodeResponseType.push, data).toJson()
                    socket.send(response)
                    socket.close()

                elif type is MasterRequestType.delete:
                    self.dir.pop(request['key'])
                    response = MasterResponse(NodeResponseType.done, '').toJson()
                    socket.send(response)
                    socket.close()

                elif type is MasterRequestType.copy:
                    # TODO: copy from src ip to dst ip
                    pass

                elif type is MasterRequestType.shutdown:
                    sys.exit()

            except Exception as ex:
                print "An exception with name \n" + str(ex) + \
                      "\n was raised. Closing socket...\n"
                socket.close()
                break

    def initiateMasterConnect(self):
        pass


def usage_error():
    print "Usage: python file_node.py -test"
    sys.exit()

def main(argc, argv):

    try:
        flag = argv[1]
    except:
        flag = "NULL"

    if flag == "-test":
        fnode = FileNode(mode = 'test')
    else:
        fnode = FileNode()

    fnode.start()

if __name__ == '__main__':
    main(len(sys.argv), sys.argv)

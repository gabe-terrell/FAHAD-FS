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
import errno
from subprocess import call
from filenode_master_protocol import *
from threaded_server import ThreadedServer

NODE_FILEPATH = "./nodefiles/"
NODESERVER_ADDR, NODESERVER_PORT  = setup.FILE_NODE_ADDR


class FileNode:

    def __init__(self, masterAddr = NODESERVER_ADDR, serverPort = NODESERVER_PORT, mode = None):

        port = NODESERVER_PORT

        for i in range(1, setup.N_COPIES):
            try:
                self.server = ThreadedServer((NODESERVER_ADDR, port), mode)
                break
            except socket.error as e:
                if e.errno is errno.EADDRINUSE:
                    port = port + 1
                else:
                    print "File node server error. Shutting down."
                    sys.exit()

        self.nodeID     = self.getNodeID()
        self.dir        = self.openDir()


    def start(self):

        target = self.__startServer
        self.server.handler = self.handleConnection
        serverThread = Thread(target=target, args=[self.server])
        serverThread.start()


    def __startServer(self, server):
        server.listen()

    def getNodeID(self):

        # dirs = os.walk(NODE_FILEPATH).next()[1]

        dirs = os.listdir(NODE_FILEPATH)
        ids = [int(re.findall('\d+', d).pop()) for d in dirs]
        data = {'ids': ids, 'port': self.server.port}
        request = Request(ReqType.n2m_wakeup, data).toJson()
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:

            clientsocket.connect(setup.MASTER_NODE_ADDR)
            clientsocket.send(request)
            print "ID REQUEST: " + request
            response = clientsocket.recv(setup.BUFSIZE)
            response = json.loads(response)

            if not 'type' in response:
                raise error("Master sent bad response.")

            if response['type'] is MastResType.wakeresponse:
                nodeID = int(response['data'])

            elif response['type'] is ResType.m2n_kill:
                print "Recieved shutdown signal from masternode. Shutting down."
                sys.exit()

            else:
                print "Recieved invalid response type from masternode."
                sys.exit()

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
            dirname = NODE_FILEPATH + "node" + str(self.nodeID) + "/"
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
        data = ''

        while True:

            try:
                data += socket.recv(setup.BUFSIZE)
                request = loads(data)
                break
            except socket.error as ex:
                print "Error reading from socket -- connection may have broken."
                socket.close()
                return
            except Exception as ex:
                print "partial read -- have not yet receved full json"
                continue

        try:

            if not data: raise error("No data received from client."):
            if not 'type' in request:
                raise error("Bad request to filenode recieved from " + str(address))
            type = request['type']

            if  type  is ReqType.store:
                handleFileStore(socket, address, request)

            elif type is ReqType.retrieve:
                handleFileRetrieve(socket, address, request)

            elif type is ReqType.delete:
                handleFileDelete(socket, address, request)

            elif type is ReqType.copy:
                handleFileCopy(socket, address, request)

            elif type is ReqType.rename:
                handleRename(socket, address, request

            elif type is ReqType.m2n_kill:
                handleKill(socket, address, request):

            else:
                raise error("Invalid request to file node from " + str(address))

        except Exception as ex:
            print "An exception with name \n" + str(ex) + \
                  "\n was raised. Closing socket...\n"
            socket.close()
            break



    def initiateMasterConnect(self):
        pass

    def handleFileStore(self, socket, address, request):

        try:
            # make sure request is good
            if not ('len' in request and 'path' in request):
                raise error("Incorrect fields present in STORE JSON.")
            elif request['len'] is None or request['path'] is None:
                raise error("Len and path fields initialized to None in STORE JSON")

            nBytes = request['len']
            if not isInstance(nBytes, int):
                raise error("Len field is not an integer in STORE request from " + str(address))

            res = Response(ResType.ok)
            socket.send(res)

            # setup to read new data

            data = bytearray()

            # read in the file
            while len(data) < nBytes:
                newBytes = socket.recv(setup.BUFSIZE)
                data.extend(newBytes.encode(encoding='utf-8'))

            self.dir[request['path']] = data
            self.saveState()

            # connect to server



        except Exception as ex:
            print "An exception with name \n" + str(ex) + \
                  "\n was raised. Closing socket...\n"
            socket.close()
            break


        pass
        # recieve len data from the socket
        # recieve more data (the file)
        # store it
        # send a hash of it to the server to confirm integrity

    def handleFileRetrieve(self, socket, address, request):
        # get file from storage
        # send it in chunks that won't be too big for ram
        pass

    def handleFileDelete(self, socket, address, request):
        # delete the file
        # confirm with masternode
        pass

    def handleFileCopy(self, socket, address, request):
        # copy the file to some new location (could even be self)
        pass

    def handleRename(self, socket, address, request:
        # rename the file (change hash key in dictionary)
        pass

    def handleKill(self, socket, address, request):
        # if the kill signal isn't from the master, don't listen
        pass

    def verify


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

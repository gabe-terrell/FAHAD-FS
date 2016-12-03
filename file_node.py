# file node for distributed file system

import os, io, re, sys, time
import socket
import pickle
import setup
import threading
import json
import errno
import hashlib
from subprocess import call
from filenode_master_protocol import *
from threaded_server import ThreadedServer
from error_handling import DFSError


NODE_FILEPATH = "./nodefiles/"
RAWFILE_EXT   = ".bin"
META_EXT      = ".meta"
DATA_ENCODING = 'utf-8'
NODESERVER_ADDR, NODESERVER_PORT  = setup.FILE_NODE_ADDR


class FileNode:

    def __init__(self, masterAddr = NODESERVER_ADDR, serverPort = NODESERVER_PORT, mode = None):

        port = NODESERVER_PORT

        for i in range(1, setup.N_COPIES):
            try:
                self.server = ThreadedServer((NODESERVER_ADDR, port),
                                             handler = self.handleConnection)
                break
            except socket.error as e:
                if e.errno is errno.EADDRINUSE:
                    port = port + 1
                else:
                    print "File node server error. Shutting down."
                    sys.exit()

        self.nodeID = None
        self.dirpath = None
        self.wakeup() # sets nodeid, gives server address, checks directory integrity


    def start(self):

        target = self.__startServer
        self.server.handler = self.handleConnection
        serverThread = Thread(target=target, args=[self.server])
        serverThread.start()


    def __startServer(self, server):
        server.listen()

    def wakeup(self):

        dirs = os.walk(NODE_FILEPATH).next()[1] # list of directories
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

            if response['type'] is ResType.m2n_wakeres:
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
        self.nodeID  = nodeID
        self.dirpath = NODE_FILEPATH + "node" + str(self.nodeID)

        if not os.path.isdir(self.dirpath):
            os.mkdir(self.dirpath)

    def start(self):
        self.server.listen()

    def handleConnection(self, sock, address):

        try:
            request = self.readJSONFromSock(sock, address)
        except:
            print "Error getting data from " + str(address) + " in 'handleConnection'"
            print "Closing socket."
            sock.close()

        # handle request
        try:
            if not 'type' in request:
                raise error("Bad request to filenode recieved from " + str(address))

            type = request['type']

            if  type  is ReqType.store:
                self.handleFileStore(sock, address, request)

            elif type is ReqType.retrieve:
                self.handleFileRetrieve(sock, address, request)

            elif type is ReqType.delete:
                self.handleFileDelete(sock, address, request)

            elif type is ReqType.copy:
                self.handleFileCopy(sock, address, request)

            elif type is ReqType.rename:
                self.handleRename(sock, address, request)

            elif type is ReqType.m2n_kill:
                self.handleKill(sock, address, request)

            else:
                raise error("Invalid request to file node from " + str(address))

        except Exception as ex:
            print "An exception in 'handleConnection' with name \n" + str(ex) + \
                  "\n was raised. Closing socket...\n"
            sock.close()
            return


    def initiateMasterConnect(self):
        pass

    def handleFileStore(self, clientSocket, address, request):

        try:
            if not ('len' in request and 'path' in request):
                raise error("Incorrect fields present in STORE JSON.")

            elif request['len'] is None or request['path'] is None:
                raise error("Len and path fields initialized to None in STORE JSON")

            nBytesExpected = request['len']
            if not isinstance(nBytesExpected, int):
                raise error("Len field is not an integer in STORE request from " + str(address))

            # hash filepath to get file handle
            path   = request['path']
            m = hashlib.md5()
            m.update(path)
            pathHashStr = str(m.hexdigest())

            chunkFilename = self.dirpath + '/' + pathHashStr + RAWFILE_EXT
            metaFilename  = self.dirpath + '/' + pathHashStr + META_EXT
            res = Response(ResType.ok)
            clientSocket.send(res.toJson())

            # read in the file
            nRecvd = 0
            h = hashlib.md5()


            with io.open(chunkFilename, 'wb') as cFile:

                while nRecvd < nBytesExpected:

                    newBytes = clientSocket.recv(setup.BUFSIZE)
                    nRecvd = nRecvd + len(newBytes)
                    print "Received " + str(nRecvd) + " of " + str(nBytesExpected) + " bytes"
                    encodedBytes = bytearray(newBytes)
                    n = cFile.write(encodedBytes)
                    h.update(encodedBytes)

            dataChecksum = h.hexdigest()

            with io.open(metaFilename, 'wb') as mFile:
                metadata = {'checksum': dataChecksum}
                mFile.write(str(metadata))

            print "Done writing file " + str(path) + " to disk..."

            # send a hash of the new file to the server to confirm integrity
            request = Request(ReqType.n2m_update,
                              data = self.nodeID,
                              path = path,
                              chksum = dataChecksum).toJson()

            # wait for verification response
            mastersock = self.reqToMaster(request)
            # res = self.readJSONFromSock(mastersock, setup.MASTER_NODE_ADDR)
            mastersock.close()

            clientSocket.close()

        except Exception as ex:
            print "An exception in 'handleFileStore' with name \n" + str(ex) + \
                  "\n was raised. Closing socket...\n"
            clientSocket.close()

    def reqToMaster(self, request):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(setup.MASTER_NODE_ADDR)
            sock.send(request)
        except socket.error as e:
            raise DFSError("Socket error in 'reqToMaster'" + \
                           " with value " + str(e) + " in function 'reqToMaster'.")
        return sock

    def readJSONFromSock(self, sock, addr):
        data = ''
        while True:
            try:
                data += sock.recv(setup.BUFSIZE)
                obj = json.loads(data)
                break
            except socket.error as ex:
                print "Error reading from socket -- connection may have broken."
                sock.close()
                return
            except Exception as ex:
                print "Partial read from " + str(addr) + " -- have not yet receved full JSON."
                time.sleep(0.5)
                continue

        if not data: raise DFSError("No data recieved in readJSONFromSock")

        return obj



    def handleFileRetrieve(self, socket, address, request):
        # get file from storage
        # send it in chunks that won't be too big for ram
        try:
            path = request['path']
            print "Received download request for " + path
            # TODO: Convert path to filenode file scheme to get the file, then send to client

            socket.close()
        except Exception as ex:
            pass

    def handleFileDelete(self, socket, address, request):
        # delete the file
        # confirm with masternode
        pass

    def handleFileCopy(self, socket, address, request):
        # copy the file to some new location (could even be self)
        pass

    def handleRename(self, socket, address, request):
        # rename the file (change hash key in dictionary)
        pass

    def handleKill(self, socket, address, request):
        # if the kill signal isn't from the master, don't listen
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

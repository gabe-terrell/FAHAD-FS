# file node for distributed file system

import os, io, re, sys, time
import socket
import pickle
import setup
import threading
import json
import errno
import hashlib
from threading import Thread
from subprocess import call
from filenode_master_protocol import *
from threaded_server import ThreadedServer
from error_handling import DFSError
from jsonsocket import readJSONFromSock



NODE_FILEPATH = str(setup.HOMEDIR) + "nodefiles/"
RAWFILE_EXT   = ".bin"
META_EXT      = ".meta"
DATA_ENCODING = 'utf-8'
NODESERVER_ADDR, NODESERVER_PORT  = setup.FILE_NODE_ADDR

class SessionLog(object):

    def __init__(self, type, size):
        self.time = time.time()
        self.type = type
        self.size = size

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
        self.log = []
        self.mode = mode
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
        if self.mode == 'fresh':
            ids = []
        else:
            ids = [int(re.findall('\d+', d).pop()) for d in dirs]
        data = {'ids': ids, 'port': self.server.port}
        request = Request(ReqType.n2m_wakeup, data).toJson()
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:

            clientsocket.connect(setup.MASTER_NODE_ADDR)
            clientsocket.send(request)
            print "ID REQUEST: " + request
            response = readJSONFromSock(clientsocket, setup.MASTER_NODE_ADDR)

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
            request = readJSONFromSock(sock, address)
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

            elif type is ReqType.n2ncopy:
                self.handleExternalFileCopy(sock, address, request)

            elif type is ReqType.rename:
                self.handleRename(sock, address, request)

            elif type is ReqType.m2n_kill:
                self.handleKill(sock, address, request)

            elif type is ReqType.ping:
                self.handleStatusCheck(sock, address, request)

            else:
                raise error("Invalid request to file node from " + str(address))

        except Exception as ex:
            print "An exception in 'handleConnection' with name \n" + str(ex) + \
                  "\n was raised. Closing socket...\n"
            sock.close()
            return

    def hashForPath(self, path):
        m = hashlib.md5()
        m.update(path)
        return str(m.hexdigest())

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
            path = request['path']
            pathHashStr = self.hashForPath(path)
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

            # Log new file download
            self.log.insert(0, SessionLog('upload', nBytesExpected))

            # send a hash of the new file to the server to confirm integrity
            request = Request(ReqType.n2m_update,
                              data = self.nodeID,
                              path = path,
                              status = True,
                              chksum = dataChecksum).toJson()

            # wait for verification response
            mastersock = self.reqToMaster(request)
            mastersock.close()

            clientSocket.close()

        except Exception as ex:
            print "An exception in 'handleFileStore' with name \n" + str(ex) + \
                  "\n was raised. Closing socket...\n"
            clientSocket.close()
            try:
                request = Request(ReqType.n2m_update,
                                  data = self.nodeID,
                                  path = path,
                                  status = False,
                                  chksum = dataChecksum).toJson()

                # wait for verification response
                mastersock = self.reqToMaster(request)
                mastersock.close()
            except Exception as ex:
                raise DFSError("Error sending failure update to master in " + \
                               "handleFileStore")

    def reqToMaster(self, request):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(setup.MASTER_NODE_ADDR)
            sock.send(request)
        except socket.error as e:
            raise DFSError("Socket error in 'reqToMaster'" + \
                           " with value " + str(e) + " in function 'reqToMaster'.")
        return sock

    def handleFileRetrieve(self, socket, address, request):
        # get file from storage
        # send it in chunks that won't be too big for ram
        try:
            path = request['path']
            print "Received download request for " + path
            pathHashStr = self.hashForPath(path)
            chunkFilename = self.dirpath + '/' + pathHashStr + RAWFILE_EXT
            print chunkFilename
            # TODO: Convert path to filenode file scheme to get the file, then send to client

            with open(chunkFilename, 'rb') as file:
                size = os.path.getsize(chunkFilename)
                ack = Response(ResType.ok, path=path, length=size)
                socket.send(ack.toJson())

                res = readJSONFromSock(socket, address)
                if res and 'type' in res and res['type'] is ResType.ok:
                    pass
                else:
                    raise DFSError("Did not receive ack from client")

                self.log.insert(0, SessionLog('download', size))

                print "Sending data to client"
                while True:
                    data = file.read(setup.BUFSIZE)
                    if data:
                        socket.send(data)
                    else:
                        break

        except Exception as ex:
            raise DFSError("Socket error in 'handleFileRetrieve'" + \
                           " with value " + str(ex) + " in function 'handleFileRetrieve'.")

        socket.close()

    def handleFileDelete(self, socket, address, request):
        print "FILE DELETE: " + str(request)
        try:
            if 'path' in request:
                path = request['path']
                hashpath = self.hashForPath(path)
                socket.close()
                rawfpath = self.dirpath + '/' + hashpath + RAWFILE_EXT
                metapath = self.dirpath + '/' + hashpath + META_EXT

                if os.path.isfile(rawfpath) and os.path.isfile(metapath):

                    os.remove(rawfpath)
                    os.remove(metapath)
                    req = Request(ReqType.n2m_update, data = self.nodeID,
                                  path = path, status = True)
                    print "Deletion success for " + str(path)
                else:
                    print "Deletion failure for " + str(path)
                    self.failureUpdate()
                    msock.close()
                    return
                msock = self.reqToMaster(req.toJson())
                msock.close()


            else:
                print "Request to delete sent with malformed request."
                print "Closing socket."

        except Exception as ex:
            raise DFSError("Error in 'handleFileDelete'" + " with value " + str(ex))
        socket.close()

    def handleFileCopy(self, socket, address, request):
        # copy the file to some new location (could even be self)
        pass

    def uploadToNode(self, hashed_path, plaintext_path, node_address):

        def connectToNode(node_address):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(node_address)
            return s

        def messageSocket(s, message):
            s.send(message.toJson())
            return readJSONFromSock(s, str(s.getpeername()))

        with io.open(hashed_path, 'rb') as file:
            size = os.path.getsize(hashed_path)
            s = connectToNode(node_address)
            res = messageSocket(s, Request(ReqType.store,
                                            path = plaintext_path, length = size))

            print "Sending data transfer request to filenode"
            if res and 'type' in res and res['type'] is ResType.ok:
                pass
            else:
                print "Did not receive ack from filenode"
                raise DFSError("No ack from filenode in 'handleExternalFileCopy'")

            print "Sending data to filenode"
            while True:
                data = file.read(setup.BUFSIZE)
                if data:
                    s.send(data)
                else:
                    break
            s.close()

    def handleExternalFileCopy(self, socket, address, request):

        try:
            if 'path' in request and 'data' in request:
                plainpath = request['path']
                addrs = request['data']
                if 'address' in addrs and 'port' in addrs:
                    ips = addrs['address']
                    ports = addrs['port']
                else:
                    self.failureUpdate(plainpath)
                    socket.close()
                    return

                print "Performing external file copy of " + str(plainpath) + " to " + str(addrs)
                hashpath = self.hashForPath(plainpath)
                rawfpath = self.dirpath + '/' + hashpath + RAWFILE_EXT

                if os.path.isfile(rawfpath):
                    target = self.uploadToNode
                    adds = [pair for pair in zip(ips, ports)]
                    print adds
                    for ad in adds:
                        args = [rawfpath, plainpath, ad]
                        uploadThread = Thread(target = target, args = args)
                        uploadThread.start()

                    # wait for server to tell you that it worked. if not,
                    # resend the file
                    while True:
                        res = readJSONFromSock(socket, setup.MASTER_NODE_ADDR)
                        if res:
                            print res['output']
                            if res['success']:
                                break
                            else:
                                address = (res['address'], res['port'])
                                args = [hashpath, plainpath, address]
                                uploadThread = Thread(target = target, args = args)
                                uploadThread.start()

                else:
                    self.failureUpdate(plainpath)
            else:
                self.failureUpdate('unknown_path')

        except Exception as e:
            raise DFSError("Error in 'handleExternalFileCopy' with value " + str(e))
        socket.close()

    def failureUpdate(self, path):
        req = Request(ReqType.n2m_update, data = self.nodeID,
                      path = path, status = False)


    def handleRename(self, socket, address, request):
        # rename the file (change hash key in dictionary)
        pass

    def handleKill(self, socket, address, request):
        # if the kill signal isn't from the master, don't listen
        pass

    def fetchFiles(self):
        return [f[:-5] for f in os.listdir(self.dirpath) if f[-5:] == '.meta']

    def fetchFilename(self, filename, ext):
        path = self.dirpath + '/' + filename + ext
        return path

    def fetchMetadata(self, filename):
        path = self.fetchFilename(filename, '.meta')
        try:
            with open(path, 'r') as file:
                data = file.read(setup.BUFSIZE).replace("'", '"')
                return json.loads(data)
        except Exception as ex:
            print "Error in fetchMetadata: " + str(ex)
            return None

    def fetchSize(self, filename):
        bin = self.fetchFilename(filename, '.bin')
        return os.path.getsize(bin)

    def fetchSizeOnDisk(self):
        size = 0
        for file in self.fetchFiles():
            size += self.fetchSize(file)
        return size

    def removeFile(self, filename):
        bin = self.fetchFilename(filename, '.bin')
        meta = self.fetchFilename(filename, '.meta')
        os.remove(bin)
        os.remove(meta)

    def validateData(self, checksums, metadata):
        errors = []
        for file in checksums:
            metaname = self.hashForPath(file)
            if metaname in metadata:
                checksum = self.fetchMetadata(metaname)['checksum']
                if checksums[file] == checksum:
                    #print file + " validated"
                    pass
                else:
                    #print file + " failed"
                    pass
                    errors.append(metaname)
                metadata.remove(metaname)
        errors.extend(metadata)
        return errors


    def fetchActivitySince(self, seconds):
        bound = time.time() - seconds
        activity = []
        for log in self.log:
            if log.time > bound:
                activity.append(log)
            else:
                return activity

    def handleStatusCheck(self, socket, address, request):
        print "Received status check from master!"

        activity = self.fetchActivitySince(10)
        if activity:
            data = []
            for a in activity:
                data.append({'type': a.type, 'size': a.size})
        else:
            data = None
            print "No activity"

        res = Response(ResType.ok, data=data, length=self.fetchSizeOnDisk())
        socket.send(res.toJson())

        data = request['data']
        errors = self.validateData(data, set(self.fetchFiles()))
        if errors:
            "Deleting " + str(len(errors)) + " obsolete files"
            for file in errors:
                self.removeFile(file)

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
    elif flag == "-fresh":
        fnode = FileNode(mode = 'fresh')
    else:
        fnode = FileNode()

    fnode.start()

if __name__ == '__main__':
    main(len(sys.argv), sys.argv)

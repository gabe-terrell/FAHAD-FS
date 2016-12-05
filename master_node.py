import sys, setup, json, os, ast, time, socket
from threading import Thread
from threaded_server import ThreadedServer
from file_structure import Directory
from client_server_protocol import ClientRequestType, ClientResponse
from filenode_master_protocol import *
from master_registry import Registry, DataRecord
from viewer import Viewer
from error_handling import DFSError

_, CLIENT_PORT = setup.MASTER_CLIENT_ADDR
_, NODE_PORT = setup.MASTER_NODE_ADDR

PING_INTERVAL = 5 # seconds

def tprint(obj):
    print obj
    sys.stdout.flush()

class UploadSession(object):

    def __init__(self, path, checksum, nodeIds, clientsocket):
        self.path = path
        self.checksum = checksum
        self.nodeIds = set(nodeIds)
        self.clientsocket = clientsocket

    def verify(self, checksum, nodeId):
        if nodeId in self.nodeIds:
            if self.checksum == checksum:
                self.nodeIds.remove(nodeId)
            else:
                return False
        return True

    def finished(self):
        return len(self.nodeIds) == 0

class MasterNode(object):

    def __init__(self, registryFile = None):

        self.root = Directory('')
        self.reg = Registry(registryFile)
        self.clientServer = ThreadedServer(setup.MASTER_CLIENT_ADDR)
        self.nodeServer = ThreadedServer(setup.MASTER_NODE_ADDR)
        self.uploadSessions = {}
        self.validateRegistry()

    def validateRegistry(self):
        for path in self.reg.data:
            path = path.split('/')
            self.root.createPath(path[1:])

    def start(self):

        target = self.__startServer

        self.clientServer.handler = self.handleClientRequest
        clientThread = Thread(target=target, args=[self.clientServer])
        clientThread.start()

        self.nodeServer.handler = self.handleNodeRequest
        nodeThread = Thread(target=target, args=[self.nodeServer])
        nodeThread.start()

        while True:
            self.runStatusCheck()
            time.sleep(PING_INTERVAL)

    def runStatusCheck(self):
        print "Running status check on filenodes"
        target = self.checkStatusOfNode
        request = Request(type = ReqType.ping, data = None).toJson()
        for node in self.reg.activenodes.values():
            thread = Thread(target=target, args=[node, request])
            thread.start()

    def checkStatusOfNode(self, node, request):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)

        try:
            sock.connect(node.address)
            sock.send(request)
            res = self.readJSONFromSock(sock, node.address)
            if res['type'] is ResType.ok:
                print "Node " + str(node.id) + " passed the status check!"
        except Exception as ex:
            print "Node " + str(node.id) + " failed to acknowledge the status check!"
            print ex
            print "Removing Node " + str(node.id) + " from active node list"
            del self.reg.activenodes[node.id]

        sock.close()

    def __startServer(self, server):
        server.listen()

    def handleClientRequest(self, socket, address):

        viewer = Viewer(self.root)

        while True:
            try:
                data = socket.recv(setup.BUFSIZE)
                if data:
                    request = json.loads(data)
                    if 'type' in request:
                        print request
                        self.processClientRequest(socket, request, request['type'], viewer)
                    else:
                        raise DFSError("Invalid Client Request")
                else:
                    raise DFSError("Client disconnected")
            except Exception as ex:
                print "Exception raised in 'handleClientRequest': \n" + str(ex)
                print "Disconnecting client."
                socket.close()
                return


    def processClientRequest(self, socket, request, type, viewer):

        if type == ClientRequestType.viewer:
            if 'command' in request:
                command = request['command']
                self.handleViewerRequest(socket, viewer, command)
            else:
                raise DFSError(("Exception raised in 'processClientRequest/viewer': \n" + str(ex)))

        elif type == ClientRequestType.download:
            try:
                path = request['serverPath']
                self.handleDownloadRequest(socket, path)
            except Exception as ex:
                raise DFSError(("Exception raised in 'processClientRequest/download': \n" + str(ex)))

        elif type == ClientRequestType.upload:
            try:
                path = request['serverPath']
                size = request['filesize']
                name = request['name']
                checksum = request['checksum']
                self.handleUploadRequest(socket, path, size, name, checksum)
            except Exception as ex:
                raise DFSError(("Exception raised in 'processClientRequest/upload': \n" + str(ex)))


        elif type == ClientRequestType.rm: # 3-way w/ filenode
            pass

        elif type == ClientRequestType.mv: # 3-way w/ filenode
            pass

        elif type == ClientRequestType.mkdir: # no filenode connection
            try:
                path = request['serverPath']
                dirname = request['name']
                wd = self.root.cd(path)
                pass


            except Exception as ex:
                raise DFSError(("Exception raised in 'processClientRequest/mkdir': \n" + str(ex)))

            # I didn't want to create a merge conflict, but I think this will work
            # It just creatively reuses code from the viewer class
            try:
                path = request['serverPath']
                dirname = request['name']
                command = ['cd', path]
                output = viewer.process(len(command), command)
                if output != None:
                    command = 'mkdir ' + dirname
                    self.handleViewerRequest(socket, viewer, command)

        elif type == ClientRequestType.rmdir: # 3-way with filenode if recursive data deletion
            try:
                path = request['serverPath']
                name = request['name']
            except Exception as ex:
                raise DFSError(("Exception raised in 'processClientRequest/rmdir': \n" + str(ex)))

        elif type == ClientRequestType.stat:
            try:
                path = request['serverPath']
                name = request['name']
                fullpath = path + name

                if fullpath in self.reg.data:
                    filedata = self.reg.data[fullpath]
                    res = ClientResponse(type = type, output = filedata, success = True)
                else:
                    errmsg = "Error: " + str(fullpath) + " does not exist."
                    res = ClientResponse(type = type, output = errmsg, success = False)

                socket.send(res.toJson())
                socket.close()

            except Exception as ex:
                raise DFSError(("Exception raised in 'processClientRequest/stat': \n" + str(ex)))

        else:
            raise error("Invalid Type Request")


    def handleViewerRequest(self, socket, viewer, command):
        tprint("Viewer Request: " + command)
        if command == 'init':
            output = 'OK'
        else:
            argv = command.split()
            output = viewer.process(len(argv), argv)
        if output and output[0] == '#':
            arg = argv[0]
            if arg == 'mkdir':
                path = output[1:]
                rec = DataRecord(path, [])
                self.reg.addFile(rec)
            output = ''
        response = ClientResponse(ClientRequestType.viewer, output, output != None)
        socket.send(response.toJson())


    def handleDownloadRequest(self, socket, path):
        node = self.findNodeWithFile(path)
        if node:
            response = ClientResponse(type = ClientRequestType.download,
                                      output = "Initiating Download...",
                                      success = True,
                                      address = node.address[0],
                                      port = node.address[1])
        else:
            response = ClientResponse(type = ClientRequestType.download,
                                      output = "File not found",
                                      success = False)
        socket.send(response.toJson())


    # TODO: Right now, this naively looks until it finds a node that owns the file
    # TODO: We should change this to give priority to more available nodes first
    def findNodeWithFile(self, path):
        if path in self.reg.data:
            record = self.reg.data[path]
            nodesWithFile = list(set(record.nodeIDList) & set(self.reg.activenodes.keys()))
            if nodesWithFile:
                nodeId = nodesWithFile[0]
                node = self.reg.activenodes[nodeId]
                return node
        return None

    def handleUploadRequest(self, socket, path, filesize, filename, checksum):


        def error(message):
            response = ClientResponse(ClientRequestType.upload, message, False)
            socket.send(response.toJson())
            tprint("Upload Failed: " + message)

        tprint("Received Request to upload " + filename + " (" + str(filesize) + ") to " + str(path))

        if path[0] == '/':
            dir = self.root.cd(path[1:].split('/'))
            if dir:
                try:
                    tprint("Sending upload ACK to client")
                    # TODO: implement node balancing to choose nodes to give to client
                    # TODO: Register session by node ids (node.id)
                    nodes = self.reg.activenodes.values()
                    addrs = [node.address[0] for node in nodes]
                    ports = [node.address[1] for node in nodes]
                    response = ClientResponse(type = ClientRequestType.upload,
                                              output = "Initiating Upload...",
                                              success = True,
                                              address = addrs,
                                              port = ports)

                    tprint("Sending upload info to client for the following nodes:")
                    for node in nodes:
                        print node.address
                    socket.send(response.toJson())
                    tprint("Upload info sent to client.")

                    serverFile = path + '/' + filename if path[-1] != '/' else path + filename
                    ids = [node.id for node in nodes]
                    session = UploadSession(serverFile, checksum, ids, socket)
                    self.uploadSessions[serverFile] = session

                    # add to tree
                    dir.files.add(filename)

                    # add to registry
                    # TODO: If one of these nodes dies before file retrieval, we'll point the client to a node
                    # that doesn't actually have the file... this either needs to be updated upon validation
                    # or we need to ping each filenode to ensure it's alive before committing (or both)
                    rec = DataRecord(serverFile, ids)
                    self.reg.addFile(rec)
                    # don't close socket because filenode-facing thread will use it to send verification ack

                except Exception as ex:
                    raise DFSError("Exception raised in 'handleUploadRequest': \n" + str(ex))
            else:
                response = ClientResponse(type = ClientRequestType.upload,
                                          output = "Invalid directory path",
                                          success = False)
                socket.send(response.toJson())
                error("Directory path was not found")
        else:
            error("Directory must start with '/'")

    def handleNodeRequest(self, socket, address):

        while True:
            try:

                data = socket.recv(setup.BUFSIZE)

                if data:

                    request = json.loads(data)

                    if not 'type' in request or not 'data' in request:
                        raise error("Filenode sent bad request.")

                    type = request['type']

                    if type is ReqType.n2m_wakeup:
                        self.handleNodeWakeup(socket, address, request)
                    elif type is ReqType.n2m_update:
                        self.handleNodeUpdate(socket, request)

                    else: raise error("Bad request of type " +  str(type) + \
                                      " to master node.")

                else:
                    print "No data received from client..."
                    sys.stdout.flush()
                    print "Client lagging or disconnected."
            except Exception, ex:
                print "An exception with name \n" + str(ex) + \
                      "\n was raised. Closing socket...\n"
                socket.close()
                break

            return

    def handleNodeWakeup(self, socket, address, request):

        try:
            data = request['data']
            query_nodes = data['ids']
            node_listening_port = data['port']

            eligible_nodes = list(set(query_nodes) - set(self.reg.activenodes.keys()))

            if not eligible_nodes:

                nodeID = self.reg.nodeIDmax + 1
                print "Recieved wakeup signal from fresh file node."
                print "Initializing node with new ID " + str(nodeID) + " and adding to registry."

            else:

                nodeID = eligible_nodes[0]
                print "Recieved wakeup signal from preexisting file node with ID " + str(nodeID) + "."
                print "Adding " + str(nodeID) + " to registry."


            res = Response(ResType.m2n_wakeres, nodeID)
            socket.send(res.toJson())
            self.reg.addNode(nodeID, (address[0], node_listening_port))
            socket.close()

        except Exception, ex:
            print "An exception with name \n" + str(ex) + \
                  "\n was raised. Sending shutdown signal to filenode."
            socket.close()
            self.killNode(nodeID)

    def handleNodeUpdate(self, socket, request):
        print "Received a node update message"
        try:
            nodeId = request['data']
            path = request['path']
            checksum = request['chksum']

            session = self.uploadSessions[path]
            if session.verify(checksum, nodeId):
                print "Node " + str(nodeId) + " has received " + path + " successfully"
                if session.finished():
                    response = ClientResponse(type = ClientRequestType.upload,
                                              output = "Upload Success",
                                              success = True)
                    session.clientsocket.send(response.toJson())
                    session.clientsocket.close()
                    # send verification response to filenode
                    # socket.send(Response(ResType.ok).toJson())
                    print "All filenodes have received " + path + " -- Disconnecting from client"
            else:
                print "Node " + str(nodeId) + " failed the checksum for " + path + " -- Requesting resend"
                node = self.reg.activenodes[nodeId]
                response = ClientResponse(type = ClientRequestType.upload,
                                          output = "Retrying Upload...",
                                          success = False,
                                          address = node.address[0],
                                          port = node.address[1])
                session.clientsocket.send(response.toJson())

        except Exception, ex:
            print "An exception in 'handleNodeUpdate' with name \n" + str(ex) + \
                  "\n was raised. Sending shutdown signal to filenode."
            socket.close()
            #self.killNode(nodeId)


    # initiate a connection to filenode by id
    # TODO: sock, clientsocket, and socket... lmao, this doesn't look right
    # def connectToNode(self, id):
    #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     clientsocket.connect(self.standbynodes[id].address)
    #     return socket

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
                time.sleep(0.01)
                continue

        if not data: 
            raise DFSError("No data recieved in readJSONFromSock")

        return obj

    def killNode(self, nid):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.rec.activenodes[nid].address)
        sock.send(Response(ResType.m2n_kill).toJson())
        sock.close()



# Should fix the silly printing issues
class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)

def main(argc, argv):
    sys.stdout = Unbuffered(sys.stdout)
    if argc > 1 and os.path.isfile(setup.DEFAULT_MASTERNODE_REGISTRY_FILENAME):
        print "Loading registry from file..."
        mnode = MasterNode(registryFile = setup.DEFAULT_MASTERNODE_REGISTRY_FILENAME)
    else:
        mnode = MasterNode()
    mnode.start()


if __name__ == '__main__':
    main(len(sys.argv), sys.argv)

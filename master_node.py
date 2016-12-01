import sys, setup, json, os, ast
from threading import Thread
from threaded_server import ThreadedServer
from file_structure import Directory, File, Node
from client_server_protocol import ClientRequestType, ClientResponse
from filenode_master_protocol import *
from master_registry import Registry, DataRecord
from viewer import Viewer
from error_handling import DFSError

_, CLIENT_PORT = setup.MASTER_CLIENT_ADDR
_, NODE_PORT = setup.MASTER_NODE_ADDR

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


    def start(self):

        target = self.__startServer

        self.clientServer.handler = self.handleClientRequest
        clientThread = Thread(target=target, args=[self.clientServer])
        clientThread.start()

        self.nodeServer.handler = self.handleNodeRequest
        nodeThread = Thread(target=target, args=[self.nodeServer])
        nodeThread.start()


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
                raise DFSError("Invalid Viewer Request")

        elif type == ClientRequestType.download:
            pass

        elif type == ClientRequestType.upload:
            try:
                path = request['serverPath']
                size = request['filesize']
                name = request['name']
                checksum = request['checksum']
                self.handleUploadRequest(socket, path, size, name, checksum)
            except Exception as ex:
                raise DFSError(("Exception raised in 'processClientRequest': \n" + str(ex)))

        else:
            raise error("Invalid Type Request")

    def handleViewerRequest(self, socket, viewer, command):
        tprint("Viewer Request: " + command)
        if command == 'init':
            output = 'OK'
        else:
            argv = command.split()
            output = viewer.process(len(argv), argv)
        response = ClientResponse(ClientRequestType.viewer, output, output != None)
        socket.send(response.toJson())


    def handleDownloadRequest(self, socket, path):
        pass

    def handleUploadRequest(self, socket, path, filesize, filename, checksum):

        tprint("Received Request to upload " + filename + " (" + str(filesize) + ") to " + path)

        def error(message):
            response = ClientResponse(ClientRequestType.upload, message, False)
            socket.send(response.toJson())
            tprint("Upload Failed: " + message)

        if path[0] == '/':
            dir = self.root.cd(path[1:].split('/'))
            if dir:
                tempfile = "./" + filename # TODO: This should be changed to the hash of the filename
                try:
                    with open(tempfile, 'w') as file:
                        # TODO: Log the data file, determine logic for getting data to node
                        tprint("Sending upload ACK to client")
                        # TODO: implement node balancing to choose nodes to give to client
                        # TODO: change from single target node to list of addresses
                        # target_node = self.reg.activenodes.values()[0]

                        # TODO: Change nodes to be the ones we choose, not all of them
                        # TODO: Register session by node ids (node.id)
                        nodes = self.reg.activenodes.values()
                        addrs = [node.address[0] for node in nodes]
                        ports = [node.address[1] for node in nodes]
                        response = ClientResponse(type = ClientRequestType.upload,
                                                  output = "Initiating Upload...",
                                                  success = True,
                                                  address = addrs,
                                                  port = ports)
                        print "Sending file to following nodes:"
                        for node in nodes:
                            print node.address
                        socket.send(response.toJson())

                        # NOTE: don't think we read again from client?
                        # TODO: is there a way to produce a callback to this thread so that
                        #       once the file nodes verify the upload with the master, we can send a success
                        #       message via the TCP connection we still have open with the client?
                        serverFile = path + '/' + filename if path[-1] != '/' else path + filename
                        ids = [node.id for node in nodes]
                        session = UploadSession(serverFile, checksum, ids, socket)
                        self.uploadSessions[serverFile] = session

                        # NOTE: File has not been closed, because it's not expected to save to master
                        tprint("Upload success!")

                        # response = ClientResponse(ClientRequestType.upload, "Upload Complete!", True)
                        # socket.send(response.toJson())

                        # add to tree
                        file = File(filename)
                        dir.files.append(file)

                        # add to registry
                        rec = DataRecord(path + filename, ids)
                        self.reg.addFile(rec)

                except Exception as ex:
                    raise DFSError("Exception raised in 'handleUploadRequest': \n" + str(ex))
            else:
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
            print "An exception with name \n" + str(ex) + \
                  "\n was raised. Sending shutdown signal to filenode."
            socket.close()
            self.killNode(nodeId)


    # initiate a connection to filenode
    def connectToNode(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect(setup.MASTER_NODE_ADDR)
        pass

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

import sys, setup, json, os, ast
from threading import Thread
from threaded_server import ThreadedServer
from file_structure import Directory, File, Node
from client_server_protocol import RequestType, ClientResponse
from filenode_master_protocol import NodeRequestType, MasterResponseType
from filenode_master_protocol import MasterResponse
from master_registry import Registry, DataRecord
from viewer import Viewer

_, CLIENT_PORT = setup.MASTER_CLIENT_ADDR
_, NODE_PORT = setup.MASTER_NODE_ADDR

def tprint(obj):
    print obj
    sys.stdout.flush()

class MasterNode():

    def __init__(self, registryFile = None):

        self.root = Directory('')
        self.reg = Registry(registryFile)
        self.clientServer = ThreadedServer(setup.MASTER_CLIENT_ADDR)
        self.nodeServer = ThreadedServer(setup.MASTER_NODE_ADDR)


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
                        self.processClientRequest(socket, request, request['type'], viewer)
                    else:
                        raise error("Invalid Client Request")
                else:
                    raise error("Client disconnected")
            except:
                socket.close()
                return

    def processClientRequest(self, socket, request, type, viewer):
        if type == RequestType.viewer:
            if 'command' in request:
                command = request['command']
                self.handleViewerRequest(socket, viewer, command)
            else:
                raise error("Invalid Viewer Request")
        elif type == RequestType.download:
            pass
        elif type == RequestType.upload:
            try:
                path = request['path']
                size = request['size']
                name = request['name']
            except:
                self.handleUploadRequest(socket, path, size, name)
        else:
            raise error("Invalid Type Request")

    def handleViewerRequest(self, socket, viewer, command):
        tprint("Viewer Request: " + command)
        if command == 'init':
            output = 'OK'
        else:
            argv = command.split()
            output = viewer.process(len(argv), argv)
        response = ClientResponse(RequestType.viewer, output, output != None)
        socket.send(response.toJson())


    def handleDownloadRequest(self, socket, path):
        pass

    def handleUploadRequest(self, socket, path, filesize, filename):

        tprint("Received Request to upload " + filename + " (" + str(filesize) + ") to" + path)

        def error(message):
            response = ClientResponse(RequestType.upload, message, False)
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
                        response = ClientResponse(RequestType.upload, "Initiating Upload...", True)
                        socket.send(response.toJson())

                        tprint("Reading content from client")
                        extraRead = 1 if filesize % setup.BUFSIZE != 0 else 0
                        receptions = (filesize / setup.BUFSIZE) + extraRead
                        for _ in range(receptions):
                            data = socket.recv(setup.BUFSIZE)
                            if data:
                                file.write(data)
                            else:
                                error("Not enough data sent")
                                return

                        # NOTE: File has not been closed, because it's not expected to save to master
                        tprint("Upload success!")

                        response = ClientResponse(RequestType.upload, "Upload Complete!", True)
                        socket.send(response.toJson())

                        file = File(filename)
                        dir.files.append(file)

                except:
                    raise error("Server Error: buffering space to save file")
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

                    if type is NodeRequestType.wakeup:
                        self.handleNodeWakeup(socket, address, request)

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
            port = data['port']

            eligible_nodes = list(set(query_nodes) - set(self.reg.activenodes.keys()))

            if not eligible_nodes:

                nodeID = self.reg.nodeIDmax + 1
                print "Recieved wakeup signal from preexisting file node with ID " + str(nodeID) + "."
                print "Adding " + str(nodeID) + " to registry."

            else:

                nodeID = eligible_nodes[0]
                print "Recieved wakeup signal from fresh file node."
                print "Initializing node " + str(nodeID) + " and adding to registry."


            response = MasterResponse(MasterResponseType.wakeresponse, nodeID)
            socket.send(response.toJson())
            self.reg.addNode(nodeID, (address, port))
            socket.close()

        except Exception, ex:
            print "An exception with name \n" + str(ex) + \
                  "\n was raised. Sending shutdown signal to filenode."
            socket.close()
            self.shutdownNode(nodeID)


    # initiate a connection to filenode
    def connectToNode(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect(setup.MASTER_NODE_ADDR)
        pass

    def shutdownNode(self, nid):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.rec.activenodes[nid].address)
        sock.send(MasterResponse(MasterResponseType.shutdown, '').toJson())
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

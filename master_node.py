import sys, setup, json
from threading import Thread
from threaded_server import ThreadedServer
from file_structure import Directory, File, Node
from client_server_protocol import RequestType, ClientResponse
from filenode_master_protocol import NodeRequestType, MasterResponseType
from viewer import Viewer

_, CLIENT_PORT = setup.MASTER_CLIENT_ADDR
_, NODE_PORT = setup.MASTER_NODE_ADDR

class MasterNode():

    def __init__(self):

        self.root = Directory('')
        self.nodes = []
        self.clientServer = ThreadedServer(CLIENT_PORT)
        self.nodeServer = ThreadedServer(NODE_PORT)

    def start(self):

        target = self.__startServer

        self.clientServer.handler = self.handleClientRequest
        clientThread = Thread(target=target, args=[self.clientServer])
        clientThread.start()

        self.nodeServer.handler = self.handleNodeStartup
        nodeThread = Thread(target=target, args=[self.nodeServer])
        nodeThread.start()


    def __startServer(self, server):
        server.listen()

    def handleClientRequest(self, socket, address):
        viewer = Viewer(self.root)

        # TODO: This is disgusting to look at right now
        while True:
            try:
                data = socket.recv(setup.BUFSIZE)

                if data:
                    request = json.loads(data)

                    if 'type' in request:
                        type = request['type']

                        if type == RequestType.viewer:
                            if 'command' in request:
                                command = request['command']
                                self.handleViewerRequest(socket, viewer, command)
                            else:
                                raise error("Invalid Command Request")
                        elif type == RequestType.download:
                            pass
                        elif type == RequestType.upload:
                            pass
                        else:
                            raise error("Invalid Type Request")
                    else:
                        raise error("Invalid Client Request")
                else:
                    raise error("Client disconnected")
            except:
                socket.close()
                return

    def handleViewerRequest(self, socket, viewer, command):
        if command == 'init':
            output = 'OK'
        else:
            argv = command.split()
            output = viewer.process(len(argv), argv)
        response = ClientResponse(RequestType.viewer, output)
        socket.send(response.toJson())


    def handleDownloadRequest(self, socket, path):
        pass

    def handleUploadRequest(self, socket, path, file):
        pass

    def handleNodeStartup(self, socket, address):

        # figure out nicer way for handling all the different request types with
        # their own functions
        while True:
            try:
                data = clisock.recv(setup.BUFSIZE)
                if data:
                    request = json.loads(data)
                    if not 'type' in request:
                        raise error("Filenode sent bad request.")

                    type = request['type']
                    if type is NodeRequestType.idquery:

                        # TODO: check request['data']
                        #       look at available dirs and check against which
                        #         nodes are already running

                        response = MasterResponse(MasterResponseType.nodeid, [1])
                        socket.send(response.toJson())
                        clisock.close()

                    elif type is NodeRequestType.upload:
                        raise error("Bad request to master node.")

                else:
                    print "No data received from client..."
                    sys.stdout.flush()
                    print "Client disconnected."
            except:
                clisock.close()




def main(argc, argv):
    # TODO
    mnode = MasterNode()
    mnode.start()


if __name__ == '__main__':
    main(len(sys.argv), sys.argv)

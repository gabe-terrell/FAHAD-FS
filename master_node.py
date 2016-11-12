import sys
from threading import Thread
from threadedServer import ThreadedServer
from file_structure import Directory, File, Node

CLIENT_PORT = 9080
NODE_PORT = 9090

class MasterNode:
	def __init__(self):
		self.root = Directory('')
		self.nodes = []
		self.clientServer = ThreadedServer(CLIENT_PORT)
		self.nodeServer = ThreadedServer(NODE_PORT)

	def start(self):
		target = self.__startServer
		
		clientServer.handler = self.handleClientRequest
		clientThread = Thread(target=target, args=[self.clientServer])
		clientThread.start()
		
		nodeServer.handler = self.handleNodeConnection
		nodeThread = Thread(target=target, args=[self.nodeServer])
		nodeThread.start()


	def __startServer(self, server):
		server.listen()

	def handleClientRequest(self, socket, address):
		# TODO: Handle upload/download request
		pass


	def handleNodeConnection(self, socket, address):
		# TODO: Handle request to create new file node
		pass






def main(argc, argv):
	# TODO
	pass


if __name__ == '__main__': 
    main(len(sys.argv), sys.argv) 
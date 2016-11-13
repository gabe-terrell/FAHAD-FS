import json

class RequestType(object):
	viewer = 1
	download = 2
	upload = 3

class ClientRequest(object):
	def __init__(self, type, command = None, serverPath = None):
		self.type = type
		self.serverPath = serverPath

	def toJson(self):
		return json.dumps({'type': self.type, 'command': self.command, 'path': self.serverPath})

class ClientResponse(object):
	def __init__(self, type, output):
		self.type = type
		self.output = output

	def toJson(self):
		return json.dumps({'type': self.type, 'output': self.output})

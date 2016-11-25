import json

class RequestType(object):
	viewer = 1
	download = 2
	upload = 3

class ClientRequest(object):
	def __init__(self, type, command = None, serverPath = None, filesize = None, name = None):
		self.type = type
		self.command = command
		self.serverPath = serverPath
		self.filesize = filesize
		self.name = name

	def toJson(self):
		return json.dumps({
			'type': self.type,
			'command': self.command,
			'path': self.serverPath,
			'size': self.filesize,
			'name': self.name
		})

class ClientResponse(object):
	def __init__(self, type, output, success):
		self.type = type
		self.output = output
		self.success = success

	def toJson(self):
		return json.dumps({
			'type': self.type,
			'output': self.output,
			'success': self.success
		})

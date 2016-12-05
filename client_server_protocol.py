import json

class JsonObject(object):
	def toJson(self):
	    return json.dumps(self, default = lambda o: o.__dict__,
	                      sort_keys = False, indent = 4)

class ClientRequestType(object):
    viewer   = 1
    download = 2
    upload   = 3
    mkdir    = 4
    rmdir    = 5
    rm       = 6
    mv       = 7
    stat     = 8
    cp       = 9

class ClientRequest(JsonObject):
    def __init__(self, type, command = None, serverPath = None, filesize = None,
                 name = None, checksum = None):

        self.type = type
        self.command = command
        self.serverPath = serverPath
        self.filesize = filesize
        self.name = name
        self.checksum = checksum

class ClientResponse(JsonObject):
    def __init__(self, type, output, success, address = None, port = None):
        self.type = type
        self.output = output
        self.success = success
        self.address = address
        self.port = port

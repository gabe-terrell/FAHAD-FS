import json

class ClientRequestType(object):
    viewer = 1
    download = 2
    upload = 3

class ClientRequest(object):
    def __init__(self, type, command = None, serverPath = None, filesize = None,
                 name = None):

        self.type = type
        self.command = command
        self.serverPath = serverPath
        self.filesize = filesize
        self.name = name

    def toJson(self):
        return json.dumps(self, default = lambda o: o.__dict__,
                          sort_keys = False, indent = 4)

class ClientResponse(object):
    def __init__(self, type, output, success, address = None, port = None):
        self.type = type
        self.output = output
        self.success = success
        self.address = address
        self.port = port

    def toJson(self):
        return json.dumps(self, default = lambda o: o.__dict__,
                          sort_keys = False, indent = 4)

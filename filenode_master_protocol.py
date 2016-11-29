import json

class NodeReqType(object):
    wakeup = 1

class MastResType(object):
    wakeresponse = 1
    shutdown = 2

class ReqType(object):
    store = 1
    shutdown = 2
    delete = 3
    retrieve = 4
    copy = 5
    rename = 6

class NodeResType(object):
    ok = 1
    push = 2
    notfound = 3
    store_error = 4

class Request(object):

    def __init__(self, type, data = None, length = None, path = None):
        self.type = type
        self.data = data
        self.len  = length
        self.path = path

    def toJson(self):
        return json.dumps(self, default = lambda o: o.__dict__,
                          sort_keys = True, indent = 4)

class Response(object):

    def __init__(self, type, data, len = None, path = None):
        self.type = type
        self.data = data
        self.len  = length
        self.path = path

    def toJson(self):
        return json.dumps(self, default = lambda o: o.__dict__,
                          sort_keys = True, indent = 4)

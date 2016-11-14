import json

class NodeRequestType(object):
    idquery = 1
    upload = 2

class MasterResponseType(object):
    nodeid = 1
    shutdown = 2


class MasterRequestType(object):
    store = 1
    shutdown = 2
    delete = 3
    get = 4
    copy = 5

class NodeResponseType(object):
    done = 1
    give = 2
    notfound = 3

class NodeRequest(object):

    def __init__(self, type, data):
        self.type = type
        self.data = data

    def toJson(self):
        if type is None:
            raise error("Cannot make uninitialized node request to JSON.")
        return json.dumps({'type': self.type, 'data': self.data})



class MasterResponse(object):

    def __init__(self, type, data):
        self.type = type
        self.data = data

    def toJson(self):
        return json.dumps({'type': self.type, 'data': self.data})



class MasterRequest(object):

    def __init__(self, type, tag, data):
        self.type = type
        self.tag  = tag
        self.data = data

    def toJson(self):
        return json.dumps({'type': self.type, 'tag': self.tag, 'data': self.data})

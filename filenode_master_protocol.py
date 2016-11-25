import json

class NodeRequestType(object):
    wakeup = 1
    upload = 2

class MasterResponseType(object):
    wakeresponse = 1
    shutdown = 2


class MasterRequestType(object):
    store = 1
    shutdown = 2
    delete = 3
    retrieve = 4
    copy = 5

class NodeResponseType(object):
    done = 1
    push = 2
    notfound = 3
    store_error = 4

class NodeRequest(object):

    def __init__(self, type, data):
        self.type = type
        self.data = data

    def toJson(self):
        return json.dumps(self, default = lambda o: o.__dict__,
                          sort_keys = True, indent = 4)

class MasterResponse(object):

    def __init__(self, type, data):
        self.type = type
        self.data = data

    def toJson(self):
        return json.dumps(self, default = lambda o: o.__dict__,
                          sort_keys = True, indent = 4)


class MasterRequest(object):

    def __init__(self, type, key, data):
        self.type = type
        self.key  = key
        self.data = data
        self.len  = len(data)

    def toJson(self):
        return json.dumps(self, default = lambda o: o.__dict__,
                          sort_keys = True, indent = 4)

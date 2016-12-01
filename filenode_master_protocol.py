import json

class ReqType(object):
    m2n_kill = 0
    n2m_update = 7
    n2m_wakeup = 8
    n2m_verify = 9
    store = 1
    delete = 3
    retrieve = 4
    copy = 5
    rename = 6


class ResType(object):
    m2n_kill = 0
    m2n_wakeres = 5
    ok = 1
    push = 2
    notfound = 3
    store_error = 4



class Request(object):

    def __init__(self, type, data = None, length = None, path = None, chksum = None):
        self.type = type
        self.data = data
        self.len  = length
        self.path = path
        self.chksum = chksum

    def toJson(self):
        return json.dumps(self, default = lambda o: o.__dict__,
                          sort_keys = True, indent = 4)

class Response(object):

    def __init__(self, type, data = None, length = None, path = None):
        self.type = type
        self.data = data
        self.len  = length
        self.path = path

    def toJson(self):
        return json.dumps(self, default = lambda o: o.__dict__,
                          sort_keys = True, indent = 4)

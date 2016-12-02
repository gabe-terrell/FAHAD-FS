import json
from client_server_protocol import JsonObject

class ReqType(object):
    m2n_kill = 0
    n2m_update = 7
    n2m_wakeup = 8
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



class Request(JsonObject):

    def __init__(self, type, data = None, length = None, path = None, chksum = None):
        self.type = type
        self.data = data
        self.len  = length
        self.path = path
        self.chksum = chksum

class Response(JsonObject):

    def __init__(self, type, data = None, length = None, path = None):
        self.type = type
        self.data = data
        self.len  = length
        self.path = path

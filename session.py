class Session(object):

    def __init__(self, path, type, nodeIDs, clientsocket, dir, checksum = None):
        self.path = path
        self.type = type
        self.checksum = checksum
        self.nodeIDs = set(nodeIDs)
        self.clientsocket = clientsocket
        self.dir = dir
        self.nTriesLeft = 3 # number of tries we get to accomplish session goal

    def verify(self, checksum, nodeId):
        if nodeId in self.nodeIDs:
            if self.checksum == checksum or self.checksum is None:
                self.nodeIDs.remove(nodeId)
            else:
                return False
        return True

    def finished(self):
        return len(self.nodeIDs) == 0

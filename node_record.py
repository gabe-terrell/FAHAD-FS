import setup
import pickle
import time

class NodeRec(object):

    def __init__(self, nodeID, (IP, PORT)):
        self.id = nodeID
        self.lastModified = time.time()
        self.timeCreated = self.lastModified
        self.address = (IP, PORT)
        self.diskUsage = 0
        self.hits = 0

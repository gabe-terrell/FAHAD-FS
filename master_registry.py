import setup
import pickle
import time
from node_record import NodeRec
import hashlib

class DataRecord(object):

    def __init__(self, filepath, nodeIDList, sock = None):
        self.filepath     = filepath
        self.nodeIDList   = nodeIDList
        self.timecreated  = time.time()
        self.timemodified = self.timecreated
        self.timeaccessed = self.timecreated
        self.verified     = False
        self.tempsock     = sock
        cs = hashlib.md5()
        cs.update(path)
        self.checksum = str(cs.hexdigest())


class Registry(object):

    def __init__(self, archivePath = None):

        self.data = {}
        self.activenodes  = {}
        self.standbynodes = {}
        self.nodeIDmax    = 0

        if archivePath is not None:
            self.archivePath = archivePath
            self.loadArchive(archivePath)
        else:
            self.archivePath = setup.DEFAULT_MASTERNODE_REGISTRY_FILENAME
            self.createArchive()


    def loadArchive(self):

        try:
            file = open(self.archivePath, 'rwb+')
            arch = pickle.load(file)
            self.data = arch['data']
            self.standbynodes = arch['nodes']
            ids = [n.id for n in self.standbynodes]
            self.nodeIDmax = max(ids)
            file.close()

        except Exception as ex:

            print "Error loading masternode state from file."
            print "Please repair the masternode archive and try again."
            print "Shutting down."
            sys.exit()


    def createArchive(self):

        # NOTE: files are keyed off of their path in the client-facing filesystem
        #       each record is stored as a sub-dictionary
        #       we could support multiple USERS by creating a registry for each user

        self.data = {}
        self.saveState()

    def saveState(self):
        arch = {'data': self.data,
                'nodes': self.standbynodes}
        with open(self.archivePath, 'wb') as file:
            pickle.dump(arch, file)

    def addFile(self, rec):
        self.data[rec.filename] = rec
        self.saveState()


    def addNode(self, nodeID, (ip, port)):
        nr = NodeRec(nodeID, (ip, port))
        self.activenodes[nodeID] = nr
        self.standbynodes[nodeID] = nr
        self.nodeIDmax = max(self.nodeIDmax, nodeID)
        self.saveState()

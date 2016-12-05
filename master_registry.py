import setup, sys
import pickle
import time
from node_record import NodeRec
import hashlib
from error_handling import DFSError

class DataRecord(object):

    def __init__(self, filepath, nodeIDList):
        try:
            self.filepath     = filepath
            self.nodeIDList   = nodeIDList
            self.timecreated  = time.time()
            self.timemodified = self.timecreated
            self.timeaccessed = self.timecreated
            cs = hashlib.md5()
            cs.update(filepath)
            self.checksum = str(cs.hexdigest())
        except Exception as e:
            raise DFSError("Error initializing DataRecord for file " + str(filepath) +
                           " with exception " + str(e))

    def toJSON(self):
	    return json.dumps(self, default = lambda o: o.__dict__,
                          sort_keys = False, indent = 4)



class Registry(object):

    def __init__(self, archivePath = None):

        self.data = {}
        self.activenodes  = {}
        self.standbynodes = {}
        self.nodeIDmax    = 0

        if archivePath is not None:
            self.archivePath = archivePath
            self.loadArchive()
        else:
            self.archivePath = setup.DEFAULT_MASTERNODE_REGISTRY_FILENAME
            self.createArchive()


    def loadArchive(self):

        try:
            file = open(self.archivePath, 'rwb+')
            arch = pickle.load(file)
            self.data = arch['data']
            self.standbynodes = arch['nodes']
            ids = [n for n in self.standbynodes]
            self.nodeIDmax = max(ids) if ids else 0
            file.close()

        except Exception as ex:

            print "Error loading masternode state from file."
            print ex
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
        self.data[rec.filepath] = rec
        self.saveState()


    def addNode(self, nodeID, (ip, port)):
        nr = NodeRec(nodeID, (ip, port))
        self.activenodes[nodeID] = nr
        self.standbynodes[nodeID] = nr
        self.nodeIDmax = max(self.nodeIDmax, nodeID)
        self.saveState()

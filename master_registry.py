import setup
import pickle
import time

class Record(object):

    def __init__(self, filename, nodeIDList, file = None):
        self.filename     = filename
        self.nodeIDList   = nodeIDList
        self.file         = file # option to store
        self.timecreated  = time.time() # created now
        self.timemodified = self.timecreated
        self.timeaccessed = self.timecreated

    def toDict(self):
        return {'filename': self.filename, 'nodeIDList': self.nodeIDList}

class Registry(object):

    def __init__(self, archivePath = None):

        self.data = None

        if archivePath is not None:
            self.archivePath = archivePath
            self.loadArchive(archivePath)
        else:
            self.archivePath = setup.DEFAULT_MASTERNODE_REGISTRY_FILENAME
            self.archivePath = self.createArchive()

    def loadArchive(self):
        pass

    def createArchive(self):
        # NOTE: files are keyed off of their path in the client-facing filesystem
        #       each record is stored as a sub-dictionary
        #       we could support multiple USERS by creating a registry for each user

        self.data = {}
        self.saveState()

    def saveState(self):
        # pickle.dump(self.data, self.archivePath)
        pass

    def add(self, rec):
        self.data[rec.filename] = rec.toDict()

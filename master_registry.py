import setup
import pickle

class Record(object):

    def __init__(self, filename, nodeIDList):
        self.filename = filename
        self.nodeIDList = nodeIDList

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
        newrec = Record('init.txt', [])
        self.data = {'init.txt': newrec.toDict()}
        self.saveState()

    def saveState(self):
        pass
        # pickle.dump(self.data, self.archivePath)

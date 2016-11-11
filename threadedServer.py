class threadedServer(object):

    def __init__(self, port):

        self.host = socket.gethostbyname('')
        self.port = port
        self.timeout = 60 # seconds
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def listen(self):

        self.sock.listen(5)
        while True:
            print "File node waiting for connections from the mothership..."
            clisock, cliAddr = self.sock.accept()
            clisock.settimeout(self.timeout)

            cliThread = threading.Thread( target = self.listenToClient,
                                          args   = (clisock,cliAddr))
            cliThread.start()

    def listenToClient(self, clisock, cliAddr):

        BUFSIZE = 1024

        while True:
            try:
                data = clisock.recv(BUFSIZE)
                if data:
                    response = data
                    clisock.send(response)
                else:
                    raise error("Client disconnected")
            except:
                clisock.close()

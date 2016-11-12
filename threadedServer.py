import sys, socket, threading

class ThreadedServer(object):

    def __init__(self, port, handler=None):

        self.host = socket.gethostname()
        self.port = port
        self.handler = handler
        self.timeout = 60 # seconds
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def listen(self):

        self.sock.listen(5)
        while True:
            print "File node waiting for connections from the mothership..."
            clisock, cliAddr = self.sock.accept()
            print "Connection established"
            clisock.settimeout(self.timeout)

            target = self.handler if self.handler else self.listenToClient
            cliThread = threading.Thread( target = target,
                                          args   = (clisock,cliAddr))
            cliThread.start()

    def listenToClient(self, clisock, cliAddr):

        BUFSIZE = 1024

        while True:
            try:
                data = clisock.recv(BUFSIZE)
                if data:
                    print "Received data"
                    print data
                    sys.stdout.flush()
                    response = data
                    clisock.send(response)
                else:
                    print "No data received from client"
                    sys.stdout.flush()
                    raise error("Client disconnected")
            except:
                clisock.close()
                break

if __name__ == '__main__': 
    port = 9091
    
    if len(sys.argv) > 2:
        print "Usage: threadedServer <port=9091>"
        sys.exit()
    if len(sys.argv) == 2:
        try:
            port = int(sys.argv[1])
        except:
            print "Usage: threadedServer <port=9091>"
            sys.exit()
    
    print "Listening on port " + str(port) + "..."
    server = ThreadedServer(port)
    server.listen()

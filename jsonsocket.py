import time, json, datetime, socket
from datetime import timedelta
from error_handling import DFSError
from setup import BUFSIZE, WAIT_INTERVAL

def readJSONFromSock(sock, addr):
    data = ''
    timeout_seconds = 60
    wait_until = datetime.datetime.now() + timedelta(seconds = timeout_seconds)
    while True:
        try:
            data += sock.recv(BUFSIZE)
            obj = json.loads(data)
            break
        except socket.error as ex:
            print "Error reading from socket -- connection may have broken."
            sock.close()
            raise DFSError("Socket broken in readJSONFromSock.")
            return
        except Exception as ex:
            if wait_until < datetime.datetime.now():
                print "READ TIMED OUT."
                sock.close()
                return
            time.sleep(WAIT_INTERVAL)
            continue

    if not data: raise DFSError("No data recieved in readJSONFromSock")
    print str(obj)
    return obj

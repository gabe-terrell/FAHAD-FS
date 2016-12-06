import sys, os, ntpath, socket, json, hashlib, time
from threading import Thread
import datetime
from datetime import timedelta
from error_handling import DFSError
from setup import MASTER_CLIENT_ADDR, BUFSIZE
from client_server_protocol import ClientRequestType, ClientRequest
from filenode_master_protocol import ReqType as FileRequestType
from filenode_master_protocol import ResType as FileResponseType
from filenode_master_protocol import Request as FileRequest

BUFFER_SIZE = BUFSIZE

def usage_error():
    print "Usage: client.py -v"
    print "Usage: client.py -d <sever_file_path> <local_dir>"
    print "Usage: client.py -u <local_file_path> <server_dir>"
    print "Usage: client.py --stat <server_file_path>"
    print "Usage: client.py --rm <server_file_path>"
    print "Usage: client.py --rmdir <server_dir_path>"
    print "Usage: client.py --mkdir <server_dir_path>"
    print "Usage: client.py --cp <old_server_location> <new_server_location>"
    print "Usage: client.py --mv <old_server_location> <new_server_location>"
    sys.exit()


def server_error():
    print "Error from server"
    sys.exit()

def connect_to_node(addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    return s

def connect_to_master():
    return connect_to_node(MASTER_CLIENT_ADDR)

def message_socket(s, message):
    # print "Sending to server:\n" + str(message.toJson())

    s.send(message.toJson())

    return readJSONFromSock(s, str(s.getpeername()))

def readJSONFromSock(sock, addr):
    data = ''
    timeout_seconds = 60
    wait_until = datetime.datetime.now() + timedelta(seconds = timeout_seconds)
    while True:
        try:
            data += sock.recv(BUFFER_SIZE)
            obj = json.loads(data)
            break
        except socket.error as ex:
            print "Error reading from socket -- connection may have broken."
            sock.close()
            return
        except Exception as ex:
            if wait_until < datetime.datetime.now():
                print "READ TIMED OUT."
                sock.close()
                return
            continue

    if not data:
        raise DFSError("No data recieved in readJSONFromSock")

    return obj

# command, type
def file_viewer():

    def Request(command):
        return ClientRequest(ClientRequestType.viewer, command = command)

    s = connect_to_master()
    res = message_socket(s, Request('init'))

    if 'output' in res and res['output'] == 'OK':
        print "Connected to file viewer"
        while True:
            command = raw_input()
            res = message_socket(s, Request(command))

            if 'output' in res and 'success' in res:
                output = res['output']
                success = res['success']
                if not success:
                    s.close()
                    sys.exit()
                if output:
                    print output
            else:
                server_error()
    else:
        server_error()

def filename(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def download(server_file_path, local_dir):

    file = filename(server_file_path)
    path = local_dir + '/' + file if local_dir[-1] != '/' else local_dir + file
    request = ClientRequest(ClientRequestType.download, serverPath = server_file_path)

    try:
        with open(path, 'wb') as file:
            s = connect_to_master()
            res = message_socket(s, request)

            print res
            print res['output']
            if not res['success']:
                return

            address = (res['address'], res['port'])
            download_from_socket(file, path, server_file_path, address)

    except Exception as ex:
        print "Exception raised with name: \n" + str(ex)

def download_from_socket(file, local_file_path, server_file_path, node_address):

    request = FileRequest(FileRequestType.retrieve, path=server_file_path)
    s = connect_to_node(node_address)
    res = message_socket(s, request)

    print "Sending data transfer request to filenode"
    if res and 'type' in res and res['type'] is FileResponseType.ok:
        totalBytes = res['len']
        res = FileRequest(FileResponseType.ok)
        s.send(res.toJson())
    else:
        print "Did not receive ack from filenode"
        server_error()

    nRecvd = 0
    while nRecvd < totalBytes:
        newBytes = s.recv(BUFSIZE)
        nRecvd += len(newBytes)
        print "Received " + str(nRecvd) + " of " + str(totalBytes) + " bytes"
        # encodedBytes = bytearray(newBytes)
        # n = file.write(encodedBytes)
        file.write(newBytes)

    s.close()


def upload(local_file_path, server_dir):

    def Request(path, size, name, checksum):
        return ClientRequest(ClientRequestType.upload, serverPath=path,
            filesize=size, name=name, checksum=checksum)

    def serverpath(file, path):
        return path + '/' + file if path[-1] != '/' else path + file

    try:
        with open(local_file_path, 'rb') as file:
            size = os.path.getsize(local_file_path)
            s = connect_to_master()

            # calculate checksum
            m = hashlib.md5()
            while True:
                bytes = file.read(BUFFER_SIZE)
                n = len(bytes)
                m.update(bytes)
                if BUFFER_SIZE > n: break

            checksum = m.hexdigest()

            res = message_socket(s, Request(server_dir, size, filename(local_file_path), checksum))

            print res['output']
            if not res['success']:
                return

            target = upload_to_node
            server_path = serverpath(filename(local_file_path), server_dir)
            for i in range(len(res['address'])):
                address = (res['address'][i], res['port'][i])
                args = [local_file_path, server_path, address]
                uploadThread = Thread(target=target, args=args)
                uploadThread.start()

            # Wait for upload status from server
            while True:
                response = readJSONFromSock(s, MASTER_CLIENT_ADDR)
                if response:
                    print response['output']
                    if response['success']:
                        return
                    else:
                        address = (response['address'], response['port'])
                        args = [local_file_path, server_path, address]
                        uploadThread = Thread(target=target, args=args)
                        uploadThread.start()

    except Exception as ex:
        print "Exception raised with name: \n" + str(ex)


def upload_to_node(local_file_path, server_file_path, node_address):

    def Request(path, size):
        return FileRequest(FileRequestType.store, path=path, length=size)

    with open(local_file_path, 'rb') as file:
        size = os.path.getsize(local_file_path)
        s = connect_to_node(node_address)
        res = message_socket(s, Request(server_file_path, size))

        print "Sending data transfer request to filenode"
        if res and 'type' in res and res['type'] is FileResponseType.ok:
            pass
        else:
            print "Did not receive ack from filenode"
            server_error()

        print "Sending data to filenode"
        while True:
            data = file.read(BUFFER_SIZE)
            if data:
                s.send(data)
            else:
                break

        s.close()

def stat(server_file_path):
    try:
        req = ClientRequest(type = ClientRequestType.stat,
                        serverPath = server_file_path,
                        name = '')
        s = connect_to_master()
        s.send(req.toJson())
        res = readJSONFromSock(s, 'masternode')
        if 'success' in res and res['success'] and 'output' in res:
            print res['output']
        elif not res['success']:
            print "STAT Failure."
            if 'output' in res: print res['output']

    except Exception as e:
        DFSError("Error raised in 'stat' due to exception \n" + str(ex) +
                 "\nShutting down.")
        sys.exit()

def rm(server_file_path):

    def deleteFromNode(address, server_file_path):
        filenodesock = connect_to_node(address)
        req = FileRequest(FileRequestType.delete, path = server_file_path)
        filenodesock.send(req.toJson())

    def confirmDeletion(sock):
        while True:
            print "Waiting for deletion confirmation from Master..."
            res = readJSONFromSock(s, 'masternode')

            if 'type' not in res or res['type'] is not ClientRequestType.rm:
                raise DFSError("Recieved response of incorrect type from Master.")

            if 'success' in res and res['success']:
                print "File deletion completed with message: " + str(res['output'])
                sys.exit()
            else:
                print "File deletion unsuccessful. Retrying..."
                addrs = zip(res['address'], res['port'])
                [deleteFromNode(address, server_file_path) for address in addrs]

    try:
        req = ClientRequest(ClientRequestType.rm, serverPath = server_file_path, name = '')
        s = connect_to_master()
        s.send(req.toJson())
        res = readJSONFromSock(s, 'mastenode')
        if 'success' in res and res['success']:
            addrs = zip(res['address'], res['port'])
            [deleteFromNode(address, server_file_path) for address in addrs]
            confirmDeletion(s)


        else:
            output = res['output'] if 'output' in res else None
            print output
            raise DFSError("RM failed due to failure response from server with value: " + str(output))

    except Exception as e:
        print "Error in RM while trying to remove " + str(server_file_path) + " because: "
        print str(e)
        print "Aborting..."
        sys.exit()




def mv(server_path_old, server_path_new):
    print "MV: " + str(server_path_old) + " to " + str(server_path_new)
    # put server_path_old in ServerPath
    # put server_path_new in name
    pass

def mkdir(server_dir_path, dirname):
    print "MKDIR " + str(dirname) + " in " + str(server_dir_path)
    pass

def rmdir(server_dir_path):
    print "RMDIR " + str(server)
    pass

def copy(server_path_old, server_path_new):
    print "COPY: " + str(server_path_old) + " to " + str(server_path_new)
    # put server_path_old in ServerPath
    # put server_path_new in name
    pass

def main(argc, argv):

    try:
        flag = argv[1]
    except:
        usage_error()

    if flag == "-v":
        if argc == 2:
            file_viewer()
        else:
            usage_error()

    elif flag == "-d":
        try:
            assert argc == 4
            server_file_path = argv[2]
            local_dir = argv[3]
        except:
            usage_error()
        else:
            download(server_file_path, local_dir)

    elif flag == "-u":
        try:
            assert argc == 4
            local_file_path = argv[2]
            server_dir = argv[3]
        except:
            usage_error()
        else:
            upload(local_file_path, server_dir)

    elif flag == '--rm':
        try:
            assert argc == 3
            full_server_path = argv[2]
        except:
            usage_error()
        else:
            rm(full_server_path)

    elif flag == '--rmdir':
        try:
            assert argc == 3
            full_server_path = argv[2]
        except:
            usage_error()
        else:
            rmdir(full_server_path)

    elif flag == '--cp':
        try:
            assert argc == 4
            old_path = argv[2]
            new_path = argv[3]
        except:
            usage_error()
        else:
            copy(old_path, new_path)

    elif flag == '--mv':
        try:
            assert argc == 4
            old_path = argv[2]
            new_path = argv[3]
        except:
            usage_error()
        else:
            mv(old_path, new_path)

    elif flag == '--mkdir':
        try:
            assert argc == 3
            full_server_path = argv[2]
        except:
            usage_error()
        else:
            mkdir(full_server_path)

    elif flag == '--stat':
        try:
            assert argc == 3
            full_server_path = argv[2]
        except:
            usage_error()
        else:
            stat(full_server_path)

    else:
        usage_error()

class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)

if __name__ == '__main__':
    sys.stdout = Unbuffered(sys.stdout)
    main(len(sys.argv), sys.argv)

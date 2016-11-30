import sys, os, ntpath, socket, json
from threading import Thread
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
    sys.exit()

def server_error():
    print "Error from server"
    sys.exit()

def connect_to_node(addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    return s

def connect_to_server():
    return connect_to_node(MASTER_CLIENT_ADDR)

def message_socket(s, message):
    # print "Sending to server:\n" + message.toJson()

    s.send(message.toJson())

    response = s.recv(BUFFER_SIZE)

    if response:
        return json.loads(response)
    else:
        server_error()

# command, type
def file_viewer():

    def Request(command):
        return ClientRequest(ClientRequestType.viewer, command = command)

    s = connect_to_server()
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

def download(sever_file_path, local_dir):
    print("download " + sever_file_path + " to " + local_dir)

def upload(local_file_path, server_dir):

    def Request(path, size, name):
        return ClientRequest(ClientRequestType.upload, serverPath=path, filesize=size, name=name)

    def filename(path):
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    try:
        with open(local_file_path, 'r') as file:
            size = os.path.getsize(local_file_path)
            s = connect_to_server()
            res = message_socket(s, Request(server_dir, size, filename(local_file_path)))

            if res and res['success']:
                print res['output']
            else:
                server_error()

            address = (res['address'], res['port'])
            print address
            target = upload_to_node
            args = [local_file_path, address]
            uploadThread = Thread(target=target, args=[local_file_path, address])
            uploadThread.start()

            # NOTE: do we need this now?
            # while True:
            #     request = s.recv(BUFFER_SIZE)
            #     if request:
            #         request = json.loads(request)
            #         if request['success']:
            #             print request['output']
            #             return
            #         else:
            #             address = (request['address'], request['port'])
            #             target = upload_to_node
            #             args = [local_file_path, address]
            #             uploadThread = Thread(target=target, args=[self.clientServer])
            #             uploadThread.start()
            #     else:
            #         server_error()

    except Exception as ex:
        print "Exception raised with name: \n" + str(ex)

def upload_to_node(local_file_path, node_address):

    def Request(path, size):
        return FileRequest(FileRequestType.store, path=path, length=size)

    with open(local_file_path, 'r') as file:
        size = os.path.getsize(local_file_path)
        s = connect_to_node(node_address)
        res = message_socket(s, Request(local_file_path, size))

        print "Sending store request to node"
        if res and 'type' in res and res['type'] is FileResponseType.ok:
            pass
        else:
            print "Did not receive ack from filenode"
            server_error()

        print "Sending Data to filenode"
        while True:
            data = file.read(BUFFER_SIZE)
            if data:
                s.send(data)
            else:
                break

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
            sever_file_path = argv[2]
            local_dir = argv[3]
        except:
            usage_error()
        else:
            download(sever_file_path, local_dir)

    elif flag == "-u":
        try:
            assert argc == 4
            local_file_path = argv[2]
            server_dir = argv[3]
        except:
            usage_error()
        else:
            upload(local_file_path, server_dir)

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

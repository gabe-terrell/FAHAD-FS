import sys, os, ntpath, socket, json
from setup import MASTER_CLIENT_ADDR
from client_server_protocol import RequestType, ClientRequest

BUFFER_SIZE = 1024

def usage_error():
    print "Usage: client.py -v"
    print "Usage: client.py -d <sever_file_path> <local_dir>"
    print "Usage: client.py -u <local_file_path> <server_dir>"
    sys.exit()

def server_error():
    print "Error from server"
    sys.exit()

def connect_to_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(MASTER_CLIENT_ADDR)
    return s

def message_server(s, message):
    s.send(message.toJson())
    response = s.recv(BUFFER_SIZE)
    if response:
        return json.loads(response)
    else:
        server_error()

# command, type
def file_viewer():

    def Request(command):
        return ClientRequest(RequestType.viewer, command=command)

    s = connect_to_server()
    res = message_server(s, Request('init'))

    if 'output' in res and res['output'] == 'OK':
        print "Connected to file viewer"
        while True:
            command = raw_input()
            res = message_server(s, Request(command))
            
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

    def Request(path, size):
        return ClientRequest(RequestType.upload, serverPath=path, filesize=size)

    try:
        with open(local_file_path, 'r') as file:
            size = os.path.getsize(local_file_path)
            print "File found and opened! File Size: "
            print size
            s = connect_to_server()
            res = message_server(s, Request(server_dir, size))
            print res
    except:
        print "File not found"

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

if __name__ == '__main__': 
    main(len(sys.argv), sys.argv) 
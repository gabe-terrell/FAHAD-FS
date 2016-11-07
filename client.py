import sys

def usage_error():
    print "Usage: client.py -v"
    print "Usage: client.py -d <sever_file_path> <local_dir>"
    print "Usage: client.py -u <local_file_path> <server_dir>"
    sys.exit()

def file_viewer():
    print("file viewer")


def download(sever_file_path, local_dir):
    print("download " + sever_file_path + " to " + local_dir)


def upload(local_file_path, server_dir):
    print("upload " + local_file_path + " to " + server_dir)


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
import sys
from file_structure import Directory

# ls, cd, mkdir, stat, mv, pwd, help, exit

class Viewer:
    def __init__(self, root):
        self.root = root
        self.cur_dir = root

    def run(self):
        while True:
            argv = raw_input().split()
            argc = len(argv)
            self.process(argc, argv)

    def process(self, argc, argv):
        if argc == 0:
            return

        command = argv[0]

        if command == 'ls':
            if argc != 1:
                self.usage_error()
            else:
                print self.cur_dir.ls()

        elif command == 'cd':
            if argc != 2:
                self.usage_error()
            else:
                raw_path = argv[1]
                if raw_path == '/':
                    result = self.root
                else:
                    path = raw_path.split('/')
                    if path[0] == '':
                        result = self.root.cd(path[1:])
                    else:
                        result = self.cur_dir.cd(path)
                
                if result:
                    self.cur_dir = result
                else:
                    print "No such directory"

        elif command == 'mkdir':
            if argc != 2:
                self.usage_error()
            else:
                dir_name = argv[1]
                if '/' in dir_name:
                    print "Invalid directory name"
                else:
                    self.cur_dir.mkdir(dir_name)

        elif command == 'pwd':
            if argc != 1:
                self.usage_error()
            else:
                print self.cur_dir.pwd()

        elif command == 'help':
            if argc != 1:
                self.usage_error()
            else:
                self.help()

        elif command == 'exit':
            sys.exit()

        else:
            self.usage_error()

    def usage_error(self):
        print "Invalid usage: use 'help' for valid commands"

    def help(self):
        print "Valid commands:"
        print "     - ls"
        print "     - cd <path>"
        print "     - mkdir <directory>"
        print "     - pwd"
        print "     - exit"

if __name__ == '__main__': 
    root = Directory('')
    viewer = Viewer(root)
    viewer.run()
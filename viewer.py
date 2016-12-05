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
            result = self.process(argc, argv)

            # result only returns None if exit was called
            # otherwise, ignore empty output
            if result == None:
                sys.exit()
            if result and result[0] != '#':
                print result

    def process(self, argc, argv):
        if argc == 0:
            return ''

        command = argv[0]

        if command == 'ls':
            if argc != 1:
                return self.usage_error()
            else:
                return self.cur_dir.ls()

        elif command == 'cd':
            if argc != 2:
                return self.usage_error()
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
                    return ''
                else:
                    return "No such directory"

        elif command == 'mkdir':
            if argc != 2:
                return self.usage_error()
            else:
                dir_name = argv[1]
                if '/' in dir_name:
                    return "Invalid directory name"
                else:
                    newdir = self.cur_dir.mkdir(dir_name)
                    return '#' + newdir.pwd() + '#'

        elif command == 'pwd':
            if argc != 1:
                return self.usage_error()
            else:
                return self.cur_dir.pwd()

        elif command == 'help':
            if argc != 1:
                return self.usage_error()
            else:
                return self.help()

        elif command == 'exit':
            return None

        else:
            return self.usage_error()

    def usage_error(self):
        return "Invalid usage: use 'help' for valid commands"

    def help(self):
        return (
            "Valid commands:\n"
            "     - ls\n"
            "     - cd <path>\n"
            "     - mkdir <directory>\n"
            "     - pwd\n"
            "     - exit"
            )

if __name__ == '__main__': 
    root = Directory('')
    viewer = Viewer(root)
    viewer.run()
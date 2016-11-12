class Directory:
	def __init__(self, name, parent = None):
		self.name = name
		self.parent = parent
		self.children = []
		self.files = []

	def mkdir(self, name):
		new_directory = Directory(name, self)
		self.children.append(new_directory)

	def ls(self):
		output = ""

		if self.children:
			output += "Directories: \n"
			for child in self.children:
				output += "     " + child.name + '\n'
		if self.files:
			output += "Files: \n"
			for file in self.files:
				print "     " + file.name + '\n'
		
		if not output:
			return "Directory empty"
		else:
			return output[:-1]


	def pwd(self):
		if self.parent:
			return self.parent.pwd() + self.name + "/"
		else:
			return self.name + "/"

	def cd(self, path):
		path_len = len(path)
		if path_len == 0:
			return self

		nextDir = path[0]
		path = path[1:]

		if nextDir == '' and path_len == 1:
			return self
		if nextDir == '.':
			return self.cd(path)
		if nextDir == '..':
			if self.parent:
				return self.parent.cd(path)
			else:
				return None

		child = self.get_child(nextDir)
		if child:
			return child.cd(path)
		else:
			return None

	def get_child(self, name):
		for child in self.children:
			if child.name == name:
				return child
		return None

class File:
	def __init__(self, name, nodes = []):
		self.name = name
		self.nodes = nodes

class Node:
	pass
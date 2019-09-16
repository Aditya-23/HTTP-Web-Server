from socket import *
from threading import *
from datetime import *
import os.path, time





class server:
	def __init__(self, address):
		try:
			server_sock = socket(AF_INET, SOCK_STREAM)
		except OSError:
			print("The socket couldn't be created")
		server_sock.bind(address)
		self.start_server(server_sock)

	def start_server(self, server_sock):
		server_sock.listen(20)
		while True:
			new_connection, recv_addr = server_sock.accept()
			client = Thread(group = None, target = self.run, kwargs = {'new_connection' : new_connection, 'recv_addr' : recv_addr})
			client.start()
			client.join()

	def run(self, new_connection, recv_addr):

		while True:
			message = new_connection.recv(4096).decode()
			request = self.handle_request(message)
			print(request)
			response = ""
			if request['version'] and request['method'] == "GET":
				response = self.get(request, new_connection)

		new_connection.close()

	def handle_request(self, message):
		request = {}
		message = message.split("\r\n")
		first_line = message[0].split(" ")
		#print(first_line)
		request['method'] = first_line[0]
		request['resource'] = self.handle_resource(first_line[1])
		if first_line[2] == "HTTP/1.1":
			request['version'] = True
		else:
			request['version'] = False
		for line in message[1:]:
			i = line.split(": ")
			if len(i) == 2:
				request[i[0]] = i[1]

		return request

	def get(self, request, new_connection):
		status = 200
		if "text/html" in request["Accept"]:
			try:
				file = open(request['resource'], "r")
			except OSError:
				raise OSError
			entity = file.read()
			file.close()
			entity_len = len(entity)
			response = self.generate_headers(request, status, entity_len)
			response += entity
			new_connection.send(response.encode())

		elif "image/webp" in request["Accept"]:
			try:
				file = open(request['resource'], "rb")
			except OSError:
				raise OSError
			entity = file.read()
			file.close()
			entity_len = len(entity)
			response = self.generate_headers(request, status, entity_len)
			response = response.encode()
			response += entity
			new_connection.send(response)



	def generate_headers(self, request, status, content_length):
		response = "HTTP/1.1 "
		response += str(status) + " " + "Ok" + "\r\n"
		response += "Data: " + self.curr_time() + "\r\n"
		response += "Server: Local" + "\r\n"
		response += "Last-Modified: " + self.modified(request['resource']) + "\r\n"
		response += "Content-Length: " + str(content_length) + "\r\n"
		if "text/html" in request["Accept"]:
			response += "Content-type: text/html" + "\r\n"
		elif "image/webp" in request["Accept"]:
			response += "Content-type: image/web" + "\r\n"

		response += "Connection: " + request["Connection"] + "\r\n\r\n"
		return response


	def handle_resource(self, file_path):
		if len(file_path) == 1:
			return "index.html"
		return file_path[1:]

	def curr_time(self):
		t = datetime.now()
		t = t.strftime("%a, %d %b %Y %H:%M:%S")
		return t

	def modified(self, file_path):
		t = os.path.getmtime(file_path)
		t = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(t)) + " GMT"
		return t


if __name__ == '__main__':
	host = "127.0.0.1"
	port = 7896
	address = (host, port)
	new_server = server(address)
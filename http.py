from socket import *
from threading import *
from datetime import *
import os.path, time
from urllib.parse import *

def curr_time():
		t = datetime.now()
		t = t.strftime("%a, %d %b %Y %H:%M:%S")
		return t

def modified(file_path):
	t = os.path.getmtime(file_path)
	t = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(t)) + " GMT"
	return t

class Response:
	status = {
		200 : "Ok",
		201	: "Created",
		202	: "Accepted",
		204 : "No Content",
		304 : "Not Modified",
		400 : "Bad Request",
		404 : "Not Found",
		411 : "Length required",
		412 : "Precondition Failed",
		415 : "Unsupported media Type",
	}

	file_format = {
		".html" : "text/html",
		".txt" 	: "text/html",
		".pdf"	: "application/pdf",
		".jpeg"	: "image/jpeg",
		".jpg"	: "image/jpeg",
		".ico" 	: "image/vnd.microsoft.icon",
		".mp3"	: "audio.mpeg",
		".mpeg"	: "video/mpeg",
		".odt"	: "application/vnd.oasis.opendocument.text",
		".rar"	: "application/x-rar-compressed",
		".doc"	: "application/msword",
		".docx"	: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
		".mpkg"	: "application/vnd.apple.installer+xml",
		".ods"	: "application/vnd.oasis.opendocument.spreadsheet",
		".png"	: "image/png",
		".ppt"	: "application/vnd.ms-powerpoint",
		".txt"	: "text/plain",
		".wav"	: "audio/wav",
		".weba"	: "audio/webm",
		".webm"	: "video/webm",
		".webp"	: ".webp",
		".xhtml": "application/xhtml+xml",
		".xlsx"	: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
		".xml"	: "application/xml",
		".zip"	: "application/zip",
		".avi"	: "video/x-msvideo",
		".css"	: "text/css",
		".csv"	: "text/csv",
		".gif"	: "image/gif",
	}
	html_string_for_post = '''<!DOCTYPE html>
<html>
<head>
	<title>form test</title>
</head>
<body>
	<h1> Resource created!</h1>
</body>
</html>'''


	def __init__(self, request):
		self.response = "HTTP/1.1 " + "\r\n"
		self.response += "Date: " + curr_time() + "\r\n"
		self.response += "Server: Local" + "\r\n"
		self.response += "Connection: " + request["Connection"] + "\r\n"

	def handle_200(self, request):
		index = self.response.find("\r\n")
		filename, file_extension = os.path.splitext(request["resource"])
		file_format_header = self.file_format.get(file_extension, None)
		if not file_format_header:
			return None
		self.response = self.response[:index] + "200 " + self.status[200] + self.response[index:]
		self.response += "Last-Modified: " + modified(request["resource"]) + "\r\n"
		self.response += "User-Agent: " + request['User-Agent'] + "\r\n"
		self.response += "Content-type: " + file_format_header + "\r\n"
		return self.response

	def handle_201(self, request):
		index = self.response.find("\r\n")
		self.response = self.response[:index] + "201 " + self.status[201] + self.response[index:]
		self.response += "Content-type: text/html" + "\r\n"
		self.response += "Content-Length: " + str(len(self.html_string_for_post)) + "\r\n\r\n"
		self.response += self.html_string_for_post
		return self.response

	def handle_204(self, request):
		index = self.response.find("\r\n")
		self.response = self.response[:index] + "204 " + self.status[204] + self.response[index:]
		self.response += "Last-Modified: " + modified(request['resource']) + "\r\n\r\n"
		return self.response

	def handle_304(self, request):
		index = self.response.find("\r\n")
		self.response = self.response[:index] + "304 " + self.status[304] + self.response[index:]
		self.response += "Last-Modified: " + modified(request["resource"]) + "\r\n"
		return self.response

	def handle_4xx(self, request, stat):
		f = str(stat) + ".html"
		index = self.response.find("\r\n")
		self.response = self.response[:index] + str(stat) + " " + self.status[stat] + self.response[index:]
		try:
			file = open(f, "r")
		except:
			print("The status file could not be opened")
		entity = file.read()
		l = len(entity)
		self.response += "Content-Length: " + str(l) + "\r\n"
		self.response += "Content-type: text/html" + "\r\n\r\n"
		self.response += entity
		return self.response


class server:
	methods = ["GET", "POST", "HEAD", "PUT", "DELETE", "TRACE"]

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
		BUFF_SIZE = 4096
		while True:
			recv_message = new_connection.recv(BUFF_SIZE)
			k = recv_message.split(b"\r\n\r\n")
			recv_decoded_message = k[0].decode()
			if len(k) > 1:
				body = k[1]
			request = self.handle_request(recv_decoded_message)

			if not self.is_good(request):
				message = Response(request)
				response = message.handle_4xx(request, 400)
				new_connection.send(response.encode())

			if request['version'] and request['method'] == "PUT" :
				fragments = [body]
				while True:
					data = new_connection.recv(BUFF_SIZE)
					fragments.append(data)
					if len(data) < BUFF_SIZE:
						break

				body = b"".join(fragments)
				self.put(request, body, new_connection)

			if request['version'] and request['method'] == "GET":
				self.get(request, new_connection)
			elif request['version'] and request['method'] == "HEAD":
				self.head(request, new_connection)
			elif request['version'] and request['method'] == "POST":
				self.post(request, body.decode(), new_connection)
				
		new_connection.close()

	def is_good(self, request):
		if not request['version']:
			return False
		if request['method'] not in self.methods:
			return False
		host = request.get("Host", None)
		if not host:
			return False
		return True

	def handle_request(self, recv_message):
		request = {}
		recv_message = recv_message.split("\r\n")
		first_line = recv_message[0].split(" ")
		print(first_line)
		request['method'] = first_line[0]
		request['resource'] = self.handle_URI(request, first_line[1])
		if first_line[2] == "HTTP/1.1":
			request['version'] = True
		else:
			request['version'] = False
		for line in recv_message[1:]:
			i = line.split(": ")
			if len(i) == 2:
				request[i[0]] = i[1]

		return request

	def get(self, request, new_connection):
		message = Response(request)
		if "If-Modified-Since" in request.keys() or "If-Unmodified-Since" in request.keys():
			if "If-Modified-Since" in request.keys():
				conditional_get = request['If-Modified-Since'][:-4]
			elif "If-Unmodified-Since" in request.keys():
				conditional_get = request['If-Unmodified-Since'][:-4]

			conditional_get = time.strptime(conditional_get, "%a, %d %b %Y %H:%M:%S")
			conditional_get = int(time.strftime("%s", conditional_get))
			file_modified_date = os.path.getmtime(request['resource'])
			file_modified_date = int(time.strftime("%s", time.localtime(file_modified_date)))
			if "If-Modified-Since" in request.keys() and file_modified_date <= conditional_get:
				print("No message")
				response = message.handle_304(request)
				response += "\r\n"
				new_connection.send(response.encode())
				return

			elif "If-Unmodified-Since" in request.keys() and file_modified_date >= conditional_get:
				print("modified")
				response = message.handle_412(request)
				response += "\r\n"
				new_connection.send(response.encode())
				return

		try:
			file = open(request['resource'], "rb")
		except:
			response = message.handle_4xx(request, 404)
			new_connection.send(response.encode())
			return 

		response = message.handle_200(request)
		if not response:
			response = message.handle_4xx(request, 415)
			new_connection.send(response.encode())
			return

		entity_len = os.stat(request['resource']).st_size	
		response += "Content-Length: " + str(entity_len) + "\r\n"
		response += "\r\n"
		response = response.encode()
		new_connection.send(response)
		try:
			new_connection.sendfile(file, 0)
		except BrokenPipeError :
			print("Successful")
		file.close()
		return

	def head(self, request, new_connection):
		message = Response(request)
		try:
			file = open(request['resource'], "rb")
		except:
			response = message.handle_4xx(request, 404)
			new_connection.send(response.encode())
			return 
		entity_len = os.stat(request['resource']).st_size
		response = message.handle_200(request)
		response += "Content-Length: " + str(entity_len) + "\r\n"
		response += "\r\n"
		response = response.encode()
		new_connection.send(response)
		file.close()
		return 

	def post(self, request, body, new_connection):
		message = Response(request)
		if request['Content-Type'] == "application/x-www-form-urlencoded":
			if "&" in body:
				body = body.split("&")
			if os.path.exists("wr.txt"):
				try:
					file = open("wr.txt", "a")
					for i in body:
						key, value = i.split("=")
						file.write(value)
						file.write(",")

					file.write("\r\n")
				except OSError:
					print("Some error occurred during execution of POST")
				file.close()
			else:
				try:
					file = open("wr.txt", "w")
					for i in body:
						key, value = i.split("=")
						file.write(key)
						file.write(",")
					file.write("\r\n")
					for i in body:
						key, value = i.split("=")
						file.write(value)
						file.write(",")
					file.write("\r\n")

				except OSError:
					print("Some error occurred during execution of POST")
				file.close()

		response = message.handle_201(request)
		new_connection.send(response.encode())

	def put(self, request, recv_message, new_connection):
		message = Response(request)
		if os.path.exists(request['resource']):
			status = 204
		else:
			status = 201
		try:
			file = open(request['resource'], "wb")
		except:
			print("The file could not be created/updated")
		file.write(recv_message)
		file.close()
		if status == 201:
			response = message.handle_201(request)
		elif status == 204:
			response = message.handle_204(request)
		new_connection.send(response.encode())
		return


	def handle_URI(self, request, file_path):
		if len(file_path) == 1:
			return "index.html"
		x = urlparse(file_path)
		file_path = x[2]	
		query = x[4]
		parameters = x[3]
		fragment = x[5]
		if parameters:
			print("parameters : " + parameters)

		if query:
			if "&" in query:
				query = query.split("&")
				print("query : ")
				for t in query:
					print(t)
			else:
				print("query : " + query)

		if fragment:
			print("fragment : " + fragment)

		return file_path[1:]


if __name__ == '__main__':
	host = "127.0.0.1"
	port = 7896
	address = (host, port)
	new_server = server(address)
from socket import *
from threading import *
from datetime import *
import os.path, time
from urllib.parse import *
import shutil
import config
import getpass
import os

def curr_time():#returns the current time in the required format
		t = datetime.now()
		t = t.strftime("%a, %d %b %Y %H:%M:%S")
		return t

def modified(file_path):#gets the modified time of file 
	t = os.path.getmtime(file_path)
	t = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(t)) + " GMT"
	return t

class Response:		#Class defined for headers manipulation of response object ; To be sent to the client
	status = config.status_codes
	file_format = config.FORMAT
	html_string_for_post = config.post_string

	def __init__(self, request):
		self.response = "HTTP/1.1 " + "\r\n"
		self.response += "Date: " + curr_time() + "\r\n"
		self.response += "Server: Local" + "\r\n"

	'''All the methods starting with 'handle_status' are used to handle the headers required for the 
	given status code. Only 'handle_4xx' handles the response status codes starting with 4.'''
	def handle_200(self, request): 
		filename, file_extension = os.path.splitext(request["resource"])
		file_format_header = self.file_format.get(file_extension, None)
		if not file_format_header:
			return None
		index = self.response.find("\r\n")
		self.response = self.response[:index] + "200 " + self.status[200] + self.response[index:]
		self.response += "Last-Modified: " + modified(request["resource"]) + "\r\n"
		self.response += "User-Agent: " + request['User-Agent'] + "\r\n"
		self.response += "Content-type: " + file_format_header + "\r\n"
		self.response += "Connection: " + request["Connection"] + "\r\n"
		return self.response

	def handle_201(self, request):
		index = self.response.find("\r\n")
		self.response = self.response[:index] + "201 " + self.status[201] + self.response[index:]
		self.response += "Content-type: text/html" + "\r\n"
		self.response += "Location: http://" + request['Host'] + '/' + request['resource'] + "\r\n"
		self.response += "Connection: " + request["Connection"] + "\r\n"
		self.response += "Content-Length: " + str(len(self.html_string_for_post)) + "\r\n\r\n"
		self.response += self.html_string_for_post
		return self.response

	def handle_202(self, request):
		index = self.response.find("\r\n")
		self.response = self.response[:index] + "202 " + self.status[202] + self.response[index:]
		self.response += "Connection: " + request["Connection"] + "\r\n"
		return self.response

	def handle_204(self, request):
		index = self.response.find("\r\n")
		self.response = self.response[:index] + "204 " + self.status[204] + self.response[index:]
		self.response += "Connection: " + request["Connection"] + "\r\n\r\n"
		return self.response

	def handle_304(self, request):
		index = self.response.find("\r\n")
		self.response = self.response[:index] + "304 " + self.status[304] + self.response[index:]
		self.response += "Connection: " + request["Connection"] + "\r\n"
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
		file.close()
		l = len(entity)
		self.response += "Content-Length: " + str(l) + "\r\n"
		self.response += "Content-type: text/html" + "\r\n\r\n"
		self.response += entity
		return self.response

	def handle_405(self, request):
		index = self.response.find("\r\n")
		self.response = self.response[:index] + str(stat) + " " + self.status[stat] + self.response[index:]
		return self.response

	def handle_501(self, request):
		index = self.response.find("\r\n")
		self.response = self.response[:index] + "501 " + self.status[501] + self.response[index:]
		file = open("501.html", "r")
		entity = file.read()
		file.close()
		l = len(entity)
		self.response += "Content-Length: " + str(l) + "\r\n"
		self.response += "Content-type: text/html" + "\r\n\r\n"
		self.response += entity
		return self.response

	def handle_505(self, request):
		index = self.response.find("\r\n")
		self.response = self.response[:index] + "505 " + self.status[505] + self.response[index:] + "\r\n"
		return self.response


class server: #Creates server object ready to listen to a given number of clients at the same time.

	methods = config.methods
	authorization_pass = config.auth_password

	def __init__(self, address):
		try:
			server_sock = socket(AF_INET, SOCK_STREAM)#create a TCP socket
		except OSError:
			print("The socket couldn't be created")
		server_sock.bind(address)  #Binds the socket to the given address
		self.start_server(server_sock)

	def start_server(self, server_sock):
		print("The server has started running..\n" + "Press ctrl + c to quit")
		server_sock.listen(100) #Starts listening for tcp connection
		while True:
			new_connection, recv_addr = server_sock.accept() #Connect to the requesting client
			'''The following line creates a thread for each new requesting client'''
			client = Thread(group = None, target = self.run, kwargs = {'new_connection' : new_connection, 'recv_addr' : recv_addr})
			client.start() #Start the thread dedicated to requests only from the given client

	def run(self, new_connection, recv_addr):
		BUFF_SIZE = config.buffer_size
		while True:
			recv_message = new_connection.recv(BUFF_SIZE)
			k = recv_message.split(b"\r\n\r\n", 1) #split the headers from the body
			recv_decoded_message = k[0].decode()
			if len(k) > 1:
				body = k[1]
			'''Processess the request and returns it in the form of dictionary; Key: header
			Value: Value assigned to the header.'''
			request, status = self.handle_request(recv_decoded_message) 
			if not status: #If no problem with headers.
				'''If the body is not fully received, the recv function is called repeatedly to accumulate
				the fragments in a list and then joined together.'''
				if request['version'] and request['method'] == "PUT" :
					fragments = []
					fragments.append(body)
					while True:
						data = new_connection.recv(BUFF_SIZE)
						fragments.append(data)
						if len(data) < BUFF_SIZE:
							break

					body = b"".join(fragments)
					self.put(request, body, new_connection)
				
				elif request['version'] and request['method'] == "TRACE":
					self.trace(request, k[0], new_connection)
				elif request['version'] and request['method'] == "GET":
					self.get(request, new_connection)
				elif request['version'] and request['method'] == "HEAD":
					self.head(request, new_connection)
				elif request['version'] and request['method'] == "POST":
					self.post(request, body.decode(), new_connection)
				elif request['version'] and request['method'] == "DELETE":
					self.delete(request, new_connection)
			else: #If any defect in headers
				message = Response(request)
				if status >= 400 and status < 500:
					response = message.handle_4xx(request, status)
					new_connection.send(response.encode())
				elif status == 501:
					response = message.handle_501(request)
					new_connection.send(response.encode())
				elif status == 505:
					response = message.handle_505(request)
					new_connection.send(response.encode())

		new_connection.close()

		'''Following is the function to do string processing to return the request dictionary. ''' 
	def handle_request(self, recv_message):
		request = {}
		status = None
		recv_message = recv_message.split("\r\n")
		first_line = recv_message[0].split(" ")
		request['method'] = first_line[0]
		if request['method'] not in self.methods:
			status = 501
		if len(first_line) > 1:
			if len(first_line[1]) > config.MAX_URI_LEN:
				status = 414
			else:
				if first_line[2] == "HTTP/1.1":
					request['version'] = True
				else:
					request['version'] = False
			request['resource'] = self.handle_URI(request, first_line[1]) #Handles the URL
			
		else:
			request['version'] = False
			status = 400	
		for line in recv_message[1:]:
			i = line.split(": ")
			if len(i) == 2:
				request[i[0]] = i[1]

		return request, status

	'''Following is the function to make sense of the URL. It prints the get parameters on the console if any.'''
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
				try:
					file = open("wr.txt", "a")
					for t in query:
						key, value = t.split("=")
						file.write(value)
						file.write(",")
					file.close()
				except:
					print("The file could not be opened")
					
			else:
				print("query : " + query)

		if fragment:
			print("fragment : " + fragment)

		return file_path[1:]

		'''Funtion to handle conditional GET request.'''
	def conditional_req(self, request, conditional_get, new_connection, message):
		conditional_get = time.strptime(conditional_get, "%a, %d %b %Y %H:%M:%S")
		conditional_get = int(time.strftime("%s", conditional_get))#Get the time in seconds.
		file_modified_date = os.path.getmtime(request['resource'])
		file_modified_date = int(time.strftime("%s", time.localtime(file_modified_date)))#modified in seconds.
		if os.access(request['resource'], os.R_OK):
			print("1234 5678")
			if "If-Modified-Since" in request.keys() and file_modified_date <= conditional_get:
				print("No message")
				response = message.handle_304(request)
				response += "\r\n"
				new_connection.send(response.encode())
				return True

			elif "If-Unmodified-Since" in request.keys() and file_modified_date >= conditional_get:
				print("modified")
				response = message.handle_412(request)
				response += "\r\n"
				new_connection.send(response.encode())
				return True

		return False


	def get(self, request, new_connection):
		message = Response(request)#Creates a response object
		print("GET " + request['resource'] + " HTTP/1.1" )
		if ("If-Modified-Since" or "If-Unmodified-Since") in request.keys(): #checks for conditional GET header
			if "If-Modified-Since" in request.keys():
				conditional_get = request['If-Modified-Since'][:-4]
			elif "If-Unmodified-Since" in request.keys():
				conditional_get = request['If-Unmodified-Since'][:-4]
			if self.conditional_req(request, conditional_get, new_connection, message):
				return 

		#Checks file read permission
		if not os.path.exists(request['resource']):
			response = message.handle_4xx(request, 404)
			new_connection.send(response.encode())
			return 
		if os.access(request['resource'], os.R_OK):
			response = message.handle_200(request)
			if not response:
				response = message.handle_4xx(request, 415)
				new_connection.send(response.encode())
				return

			file = open(request['resource'], "rb")
			entity_len = os.stat(request['resource']).st_size	#gets length of file content
			response += "Content-Length: " + str(entity_len) + "\r\n"
			response += "\r\n"
			response = response.encode()
			new_connection.send(response)#first send the headers
			l = new_connection.sendfile(file)# Used to send file 
			file.close()
			return
		else:#if permission is denied to the file
			response = message.handle_4xx(request, 403)
			new_connection.send(response.encode())
			return

	def head(self, request, new_connection):
		message = Response(request)#Creates a response object
		print("HEAD " + request['resource'] + " HTTP/1.1" )
		try:
			file = open(request['resource'], "rb")
		except:
			response = message.handle_4xx(request, 404)
			new_connection.send(response.encode())
			return 
		entity_len = os.stat(request['resource']).st_size #gets length of file content
		response = message.handle_200(request)
		response += "Content-Length: " + str(entity_len) + "\r\n"
		response += "\r\n"
		response = response.encode()
		new_connection.send(response)
		file.close()
		return 

	def post(self, request, body, new_connection):
		message = Response(request) #Creates a response object
		print("POST " + request['resource'] + " HTTP/1.1" )
		if request['Content-Type'] == "application/x-www-form-urlencoded":
			if "&" in body:
				body = body.split("&") #Split various key-value pairs
			if os.access("wr.txt", os.W_OK): #Check write permission
				try:
					file = open("wr.txt", "a") #open file to write key value pairs
					for i in body:
						key, value = i.split("=") 
						file.write(value)
						file.write(",")

					file.write("\r\n")
				except OSError:
					print("Some error occurred during execution of POST")
				file.close()
			else: #Write permission denied
				response = message.handle_4xx(request, 403)
				new_connection.send(response.encode())
				return

		response = message.handle_201(request)
		new_connection.send(response.encode())

	def put(self, request, recv_message, new_connection):
		message = Response(request)
		print("PUT " + request['resource'] + " HTTP/1.1" )
		user_pass = getpass.getpass(prompt = "Enter password: ")
		if user_pass != self.authorization_pass:
			print("Authentication failed")
			response = message.handle_4xx(request, 401)
			new_connection.send(response.encode())
			return 

		status = 201
		if os.path.exists(request['resource']): # if already exists status is 204 otherwise, 201
			status = 204
		try:
			file = open(request['resource'], "wb")
			file.write(recv_message)
			print("written")
			file.close()
			if status == 201:
				response = message.handle_201(request)
			elif status == 204:
				response = message.handle_204(request)
				
			new_connection.send(response.encode())
		except: #permission denied
			print("The file could not be created/updated")
			response = message.handle_4xx(request, 403)
			new_connection.send(response.encode())
			return
		
		return

	def delete(self, request, new_connection):
		message = Response(request)
		print("DELETE " + request['resource'] + " HTTP/1.1" )
		if os.path.exists(request['resource']):
			if os.access(request['resource'], os.W_OK) and os.access(request['resource'], os.R_OK):#check read-write permissions
				''' Enter the password on the console to authenticate'''
				user_pass = getpass.getpass(prompt = "Enter password: ")
				if user_pass != self.authorization_pass:
					#If wrong password => Unauthorized error
					response = message.handle_4xx(request, 401)
					new_connection.send(response.encode())
					return 
				try:
					os.remove(request['resource'])#delete the file
				except IsADirectoryError: # If its not he file but a directory : delete the whole directory.
					shutil.rmtree(request['resource'])
				response = message.handle_204(request)
				new_connection.send(response.encode())
			else:
				response = message.handle_4xx(request, 403)
				new_connection.send(response.encode())
				return
		else:
			response = message.handle_4xx(request, 404)
			new_connection.send(response.encode())

	def trace(self, request, content, new_connection):
		''' Sends the request packet as it is in the body '''
		response = "HTTP/1.1 200 Ok\r\n"
		response += "Content-Type: message/http\r\n"
		response += "Date: " + curr_time() + "\r\n"
		response += "Connection: " + request['connection'] + "\r\n\r\n"
		new_connection.send(response.encode())
		new_connection.send(content)

if __name__ == '__main__':
	address = config.address#obtain address from the configuration file
	new_server = server(address) # Create server object
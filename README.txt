											Web Server using HTTP
										    -----------------------

MIS: 111708038, 111708011
Project: Web server

How to run:
	1.Run "python3 http.py" on your console.
	2.To stop it, press ctrl + c.

1. Introduction
	The web server uses Hyper Text Transfer Protocol to receive requests and respond to them. The server follows guidelines as specified in RFC 2616. The currently implemented methods are GET, POST, PUT, HEAD, DELETE, TRACE.
	The response status codes implmented are 200, 201, 202, 204, 304, 400, 401, 403, 404, 411, 412, 414, 415, 501, 505.
	The status codes and their meanings are provided in the config.py file.

2. 	User defined classes: server, response.

3. 	Modules imported: socket, threading, os, urllib, shutil, config, getpass, datetime.

4. 	The server listens for multiple clients and a socket is created for each requesting client. A thread is 
	dedicated to each client. Each thread is run sepearately thus providing multiple requests from multiple clients at the same time.

	GET: The URL is parsed and the location of the file is searched in the given directory. If found the file is sent by creating a response object. Otherwise an appropriate error status code is sent in the header.

	POST: Typically used in form handling. The body of the request contains key-value pairs which are extracted. The server then writes the values to a file named "wr.txt".

	PUT: The body contains the file to be written to the given location.

	DELETE: The file or directory at the given URL is deleted if exists.

	HEAD: Sends only the headers containing the meta information of the file at the given URL.

	TRACE: Send the request packet as it is.

5.	File permissions are checked before accessing them. For GET, read permissions are checked. For POST 
	write permissions are checked. For DELETE, read and write permissions are checked. If allowed, the files are can be accessed, otherwise appropriate status code is sent.

6.	User authentication is done in PUT and DELETE methods. The user needs to enter password on the console 
	perform the required operation. Appropriate status code is sent if wrond password is entered.

7.	Testing:
		1. Use the audio, video, ppt, etc files (formats that are specified in the config.py file are supported) to test GET request.
		2. For POST, use forms (provided).
		3. For HEAD, DELETE, PUT use Postman application.
		4. The server is capable of running a website.

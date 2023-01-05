Examples
========
Omniserver examples, to serve as a reference to what it's capable of.

Basic Clients and Servers
-------------------------
Server.py starts 4 threaded servers, client.py interacts with them.

Server.py

.. code-block:: python

	import omniserver as omni
	import logging	
	logging.basicConfig(level=logging.DEBUG, format="%(message)s")
	
	# TCP server listening on 7896, UDP server listening on 3214
	omni.tcp_server(7896)
	omni.udp_server(3214)

	# Works basically the same as http.server, i.e. clients can make get requests for the files in its 
	# working directory/sub directories
	omni.http_server(8181, dir="/home/web") 

	# DNS server will resolve fraggle-rock.com to 10.10.10.50, everything else will be resolved to the default IP
	omni.dns_server(default_ip="192.168.100.1").add_record("fraggle-rock.com 60 IN A 10.10.10.50") # Will respond to all IPv4 queries 

	# Activate all initialized servers and block here until interrupt
	omni.servers.start_all()


Client.py

.. code-block:: python

	import omniserver as omni
	import logging	
	logging.basicConfig(level=logging.DEBUG, format="%(message)s")
	
	host = "fraggle-rock.com"

	# Resolve hostname to IP
	ip = omni.dns_client(("10.10.10.100", 53)).query("fraggle-rock.com") 

	tcp_client = omni.tcp_client((ip, 7896))

	if tcp_client.beacon(freq=3, tries=5): # Try to connect 5 times, 3 seconds apart	
		with omni.http_client((ip, 8181)) as http, omni.udp_client((ip, 3214)) as udp:
			http.get("/test.txt")
			udp.send("UDP client message")
			http.get("/test2.txt")
			udp.recv()
			http.get("/test3.txt")
			
		tcp_client.send("TCP client message")
		tcp_client.recv()
		tcp_client.close()
	


TLS Encrypted
-------------
Create a certificate, download to client, connect via TLS

Server.py

.. code-block:: python

	import omniserver as omni
	import logging	
	logging.basicConfig(level=logging.DEBUG, format="%(message)s")
	
	# Generate CA and private key
	cert, key = omni.certs.create_cert_key(cert="blart.crt", C="US", ST="CA", L="Fresno", O="The Mall", CN="paul-blart.edu")

	# TLS web server using an old cert (won't be checked)
	omni.http_server(443, tls=True, certfile="./data/remCA.crt", keyfile="./data/remkey.key").start()

	# Start DNS server, with a record to resolve requests for paul-blart.edu, the domain of our new cert
	omni.dns_server(record="paul-blart.edu 30 IN A 10.10.10.50").start()

	# Start TLS TCP server using previously generated cert
	omni.tcp_server(8484, tls=True, certfile=cert, keyfile=key).start()

	# Block until interrupt
	omni.servers.wait_all()
	
	
Client.py

.. code-block:: python

	import omniserver as omni
	import logging	
	logging.basicConfig(level=logging.DEBUG, format="%(message)s")
	
	# Establish TLS connection with webserver, without checking/verifying its certificate
	with omni.http_client(("10.10.10.50", 443), tls=True, cert_required=False) as https:
		https.get("/blart.crt") # Get certificate file
		
	# Establish another connection, but verifying the cert against the one we just downloaded	
	with omni.tcp_client(("paul-blart.edu", 8484), tls=True, ca_cert="./blart.crt") as tcp:
		tcp.send("TLS message")
		tcp.recv()



Command n' Control
------------------
A C2 server and client with encoded communications.

Server.py

.. code-block:: python

	class C2ServerHandler(omni.TCPHandler):
		def setup(self):
			super().setup()
			self.verified = False

		def incoming(self, data): # Decode data, the opposite of the encoding scheme
			if data:
				data = dynabyte.load(data).XOR(0x15).ROL(0x3).ADD(0x1C).getdata("string")
			return data
			
		def outgoing(self, data): # Encode data
			return dynabyte.load(data).SUB(0x1C).ROR(0x3).XOR(0x15).getdata("bytes")

		def run_cmd(self, cmd):
			cmd_output = subprocess.run(cmd, shell=True, capture_output=True).stdout.strip()
			if cmd_output == b"":
				cmd_output = b"Invalid command"
			return cmd_output

		def response(self, data): # Return a response based on recieved data (called by handle())
			if data == "password":
				self.verified = True
				return "All aboard"
			elif self.verified:
				return self.run_cmd(data)
			else:
				return "Default response"

	omni.tcp_server(9874, Handler=C2ServerHandler).start().wait()


Client.py

.. code-block:: python

	class C2Client(omni.TCPClient):
		def incoming(self, data):
			if data:
				data = dynabyte.load(data).XOR(0x15).ROL(0x3).ADD(0x1C).getdata("string")
			return data
			
		def outgoing(self, data):
			return dynabyte.load(data).SUB(0x1C).ROR(0x3).XOR(0x15).getdata("bytes")

	commands = ["dir", "whoami", "netstat -l"]

	with omni.tcp_client(("10.10.10.50", 9874), Handler=C2Client) as client:
		client.send("password")
		if client.recv()  == "All aboard":
			for cmd in commands:
				client.send(cmd)
				print(client.recv())
				
				
				
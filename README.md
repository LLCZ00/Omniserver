# Omniserver
### _Connections for all occasions_
*Omniserver* is a Python module designed for quickly prototyping controllers/intercepting malicious network communications, and replicating various types of backdoor traffic. It is capable of quickly starting up highly customizable client and server objects, the goal being to provide maximum flexibility with the smallest amount of boilerplate code possible.
## Basic Usage
See [*documentation*](https://omniserver.readthedocs.io/en/latest/)

The *omniserver* module can be used to initiate and control client and server objects. Current varieties include TCP, UDP, HTTP, and DNS.
### Clients
Client objects can be used to establish connections with remote servers. Using the *with* keyword will automatically call *connect()* and *close()* methods on the socket.
```py
import omniserver as omni

with omni.tcp_client(("192.168.1.40", 7896)) as client: 
	client.send("Akon")
	client.recv()
	client.send("All on the floor")
	
client = omni.tcp_client(("192.168.1.40", 6547))
if client.beacon(freq=3, tries=5): # Try to connect 5 times, 3 seconds apart, before quiting 
	client.send("whoami")
	client.recv()
	client.send("dir")
	client.recv()
	client.close() # Good practice, but not necessarily required
```
### Servers
Server objects create listening sockets, which await requests from remote clients. They are threaded by default, and can be run all at once or indivdually.
```py
omni.tcp_server(7896)
omni.tcp_server() # Random High Port
omni.udp_server(3214)
omni.http_server(8181) # Works basically the same as http.server
omni.dns_server(default_ip="192.168.1.40") # Will respond to all IPv4 queries with default IP
omni.servers.start_all()
```
### Inheritable Handler Classes
Client and server handler classes can be subclassed for greater control over data handling and the object in general. For example, the TCP and UDP handler's *send()* and *recv()* methods are wrapped by the *outgoing()* and *incoming()* methods, respectively. See documentation for greater details on base classes and overridable methods.
```py
import dynabyte

class C2Handler(omni.TCPHandler):
    def incoming(self, data): # Decode commands
        decoded = dynabyte.load(data).ADD(0x10).XOR(0x6A) # The encoding scheme, backwards
        return decoded.getdata("string")
        
    def outgoing(self, resp): # Encode response
        encoded = dynabyte.load(resp).XOR(0x6A).SUB(0x10) # XOR/SUB'ing all sent data
        return encoded.getdata("bytes")

class C2Client(omni.TCPClient):
    def incoming(self, data): # incoming() and outgoing() are called within recv() and send(), respectively
        decoded = dynabyte.load(data).ADD(0x10).XOR(0x6A) # The encoding scheme, backwards
        return decoded.getdata("string")

    def outgoing(self, resp): # Called whenever send() is
        encoded = dynabyte.load(resp).XOR(0x6A).SUB(0x10) # XOR/SUB'ing all sent data
        return encoded.getdata("bytes")
		
# Start server
omni.tcp_server(7896, Handler=C2Handler).start()

with omni.tcp_client(("10.10.10.100", 7896), Handler=C2Client) as client:
	client.send("Encoded message")
	client.recv()
```
Request handler classes operate basically the same way as their socketserver counterparts, handle(), setup(), finish() etc. can be overriden as you see fit.
### TLS/SSL
TCP-based servers and clients are TLS/SSL compatible. *Omniserver* provides functions for generating SSL certs, but they are currently only available when used on Linux.
```py
cert, key = omni.create_cert_key(CN="booberry.edu") # Returns absolute path to CA cert and private key
omni.tcp_server(6547, tls=True, certfile=cert, keyfile=key).start().wait()
```
On the client side, you'll need the CA of the server you plan to connect to, or cert checking can simply be disabled.
```py
# No cert required
with omni.tcp_client(("10.10.10.50", 6547), tls=True, cert_required=False) as client:
    client.send("Secret TLS message (didn't check the cert)")
    client.recv()
	
# Cert required
client = omni.tcp_client(("10.10.10.50", 6547), tls=True, hostname="booberry.edu", ca_cert="./cert.crt")
if client.connect():
    client.send("Secret TLS message")
    client.recv()
    client.close()
```
## Installation
Install from PyPI
```
pip install omniserver
```
## Known Issues & TODO
- Currently cannot easily create SSL certificates on Windows
	- Generating the cert/key with OpenSSL on Linux and moving them over works, if you truly need the TLS/SSL server on Windows
- Add function for signing certificates with CA
- HTTP server and client arn't very fleshed out, it's kinda just easier to use requests
	- HTTP/HTTPS clients and servers don't currently support sessions
- DNS over TCP is in there, but I haven't tested it extensively 
- May re-impliment CLI tool
- Fix/complete documentation (I rushed it)
- Fix overriding setup()


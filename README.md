# Omniserver
![PyPI](https://img.shields.io/pypi/v/omniserver)
### _Connections for all occasions_
*Omniserver* is a Python module designed for quickly creating highly customizable server/client objects, and to provide maximum flexibility using as little boilerplate code as possible. Common uses include prototyping/replicating malicious network communication methods, intercepting/controlling the traffic of "Command and Control"-type malware, or simply being a shortcut for general networking activities.

At its core, *omniserver* is essentially just a wrapper around Python's built-in *socketserver* module (which itself is just a wrapper around *socket*). The goal of *omniserver* is to extend *socketserver* by providing a wider variety of functions, and perhaps a simpler API. All of *omniserver*'s RequestHandler and Server objects are compatible with *socketserver*, and can basically be used in the same way as described in their documentation.
## Basic Usage
See [*documentation*](https://omniserver.readthedocs.io/en/latest/)

The *omniserver* module can be used to initiate and control client and server objects. Current varieties include TCP, UDP, HTTP, and DNS (TCP or UDP). TLS/SSL can also be enabled on any TCP-based client or server object.
### Clients
Connections can be established with remote servers using *client* objects. After succesfully connecting to a server using the *connect()* or *beacon()* methods, TCP and UDP communications are primarily controlled using the *send()* and *recv()* methods. Additionally, DNS and HTTP clients provide the *query()* and *get()* methods (respectively), which handle both the sending and recieving of their more specialized data structures.
```py
import omniserver as omni

with omni.udp_client(("192.168.1.40", 7896)) as udp_client: # 'with' keyword calls connect() and close()
	udp_client.send("Akon")
	udp_client.recv()
	udp_client.send("All on the floor")
	
tcp_client = omni.tcp_client(("192.168.1.40", 6547))
if tcp_client.beacon(freq=3, tries=5): # Try to connect 5 times, 3 seconds apart, before quiting 
	tcp_client.send("whoami")
	tcp_client.recv()
	tcp_client.send("dir")
	tcp_client.recv()
	tcp_client.close() # Good practice, but not necessarily required
	
ip = omni.dns_client(("10.10.10.100", 53)).query("fraggle-rock.com") # query() returns the resolved IP as a string
with omni.http_client((ip, 8181)) as http_client:
    http_client.get("/test.txt")
```
### Servers
Connections from remote clients can be accepted on a listening socket using *server* objects. They are threaded by default, and can be run all at once or indivdually. All *server* objects provide the same methods as their *socketserver* counterparts, with the addition of *start()*, *wait()*, and *stop()* methods. *Omniserver* also provides the *start_all()*, *wait_all()*, and *stop_all()* functions, which affect all the currently initialized servers objects at once. Server processes/threads can be exited with CTRL-C.
```py
omni.tcp_server(7896)
omni.udp_server(3214)
omni.http_server(8181) # Works basically the same as http.server
omni.dns_server(default_ip="192.168.1.40") # Will respond to all IPv4 queries with default IP
omni.servers.start_all()

tcp = omni.tcp_server.start() # Non-blocking
omni.udp_server().serve_forever() # Random high port, blocking
tcp.stop() # Shutdown tcp server after udp_server exits
```
### Customizing Request Handler Classes
*Client* and *server* handler classes can be subclassed the same way as described in *socketserver*'s documentation. All data which flows through *omniserver* objects is passed through the *incoming()* and *outgoing()* methods, so overriding them provides a convenient way to deal with encypted communications, as shown in the following example:
```py
import dynabyte

class C2Handler(omni.TCPHandler):
    def incoming(self, data): 
        return Array(data).XOR("Secret_key").ADD(0xA1).ROR(5) # The encryption scheme, backwords
        
    def outgoing(self, resp): # Encode response
        return bytes(Array(resp).ROL(5).SUB(0xA1).XOR("Secret_key")) # ROL/SUB/XOR'ing all sent data
        
    def response(self, data):
        if data == "name":
            return "Don Cheadle"
        elif data == "real name":
            return "Tiger Woods"
        else:
            return "default"

class C2Client(omni.TCPClient):
    def incoming(self, data): # incoming() and outgoing() are called within recv() and send(), respectively
        return Array(data).XOR("Secret_key").ADD(0xA1).ROR(5)

    def outgoing(self, data): # Called whenever send() is
        return bytes(Array(data).ROL(5).SUB(0xA1).XOR("Secret_key"))
		
# Start server
omni.tcp_server(6547, RequestHandler=C2Handler).start()

with omni.tcp_client(("10.10.10.100", 6547), Handler=C2Client) as tcp:
    tcp.send("name")
    tcp.recv()
    tcp.send("real name")
    tcp.recv()
    tcp.send("didgeridoo")
    tcp.recv()
```
Request handler classes operate basically the same way as their socketserver counterparts, handle(), setup(), finish() etc. can be overriden as you see fit.
### TLS/SSL
TCP-based servers and clients are TLS/SSL compatible. *Omniserver* provides functions for generating SSL certs, but they are currently only available when used on Linux.
```py
cert, key = omni.certs.create_cert_key(CN="booberry.edu") # Returns absolute path to CA cert and private key
context = omni.certs.create_server_context(certfile=cert, keyfile=key)
omni.tcp_server(6547, sslcontext=context).start().wait()
```
On the client side, you'll need the CA of the server you plan to connect to, or cert checking can simply be disabled.
```py
# No cert required
with omni.tcp_client(("10.10.10.50", 6547)) as client:
    client.enable_ssl(cert_required=False)
    client.send("Secret TLS message (didn't check the cert)")
    client.recv()
	
# Cert required
client = omni.tcp_client(("10.10.10.50", 6547), hostname="booberry.edu")
client.enable_ssl(omni.certs.create_client_context(ca_cert="./cert.crt"))
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
- DNS over TCP is in there, but I haven't tested it extensively 
- TCP servers sometimes do a weird retransmission of FIN, ACK packet
- **kwargs in client.enable_ssl(), for creating context
- Finish documentation


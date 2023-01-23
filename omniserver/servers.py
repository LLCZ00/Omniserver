#
# Copyright (C) 2023 LLCZ00
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.  
#
"""
omniserver.servers:
    - Server and RequestHandler classes
    - DNS MixIns for RequestHandler and Client classes,
        - Extends classes to provide DNS-specific functionality

Main inheritable classes:
    TCPHandler
    UDPHandler
    DNSHandler
    DNSHandlerTCP
    HTTPHandler

TODO:

"""    
import socketserver
import socket
import threading
import sys
import os
from time import sleep
from dnslib import DNSRecord,RR,A,RCODE,QTYPE
from http.server import SimpleHTTPRequestHandler

from omniserver.version import __version__

__all__ = ["TCPHandler", "UDPHandler", "DNSHandlerTCP",
            "DNSHandler", "HTTPHandler"]

"""Base Classes
- Inherited by RequestHandler and Server subclasses in omniserver.servers to provide overridable data handling methods
"""

class ThreadedBaseServer(socketserver.ThreadingMixIn, socketserver.BaseServer):
    """Base class for TCP and UDP server classes
    """
    allow_reuse_address = True
    proto = "Generic"
    verbose=True
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.active = False
        
    def __str__(self):
        return f"{self.proto} Server {self.server_address[0]}:{self.server_address[1]}"
        
    def activate(self):
        """Bind socket and activate server
        """
        if not self.active: # Don't call bind or server_activate if they've already been called (error)
            try:
                self.server_bind()
                self.server_activate() # Enable listening
            except:
                self.server_close()
                print(f"{self} Binding/activation failed")
                raise
            else:
                self.active = True
                if self.verbose:
                    print(f"{self} started...")
                    
    def serve_forever(self, poll_interval=0.5):
        """Overriding socketserver method to ensure socket
        is activated
        """
        if not self.active:
            self.activate()
        try:
            super().serve_forever(poll_interval)
        except KeyboardInterrupt: # CTRL-C to exit without raising errors
            self.shutdown()
        
    def handle_request(self):
        """Handle one request, overriding socketserver
        method to ensure socket is activated
        """
        if not self.active:
            self.activate()
        super().handle_request()
 

class BaseRequestHandler:
    """Base class for RequestHandler classes, basically an extension 
    of socketserver.BaseRequestHandler
    
    Sub classes must override send() and recv() with their protocol-specific implimentation.
    The send/recv and send_data/recv_data methods are seperated so as to easily allow 
    for bypassing the incoming/outgoing filter methods, if necessary.
    """
    keepalive = True
    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.proto = server.proto if hasattr(server, "proto") else ""
        self.verbose = server.verbose if hasattr(server, "verbose") else True
        
        self.setup()
        try:
            self.handle()
        finally:
            self.finish()
            
    def setup(self):
        """Called before handle
        """
        pass
        
    def handle(self):
        """Called by socketserver upon connection/request
        
        Keeps connection alive with client if 'keepalive' is
        True, otherwise connection is closed between each request.
        Overriding is not necessary, unless you don't want to use
        the typical 'recv, send' communication pattern.
        """        
        try:
            while True:
                data = self.recv_data()
                if not data:
                    break   
                response = self.response(data)
                self.send_data(response)
                if not self.keepalive:
                    break
        except Exception as e:
            print(f"Exception occured within {self.proto} server")
            if self.verbose:
                print(e)
        
    def finish(self):
        """Called after handle
        """
        pass
            
    def send(self, data):
        """Override with protocol/use specific send method
        
        Use directly to bypass outgoing()
        """
        raise NotImplementedError
        
    def outgoing(self, resp): # Encode data to be sent
        """Process outgoing response/data before it's sent
        
        Default: encode data and add newline
        """
        if type(resp) is not bytes:
            resp = f"{resp}\n".encode("utf-8")
        return resp
        
    def send_data(self, resp):
        """Main method to be used for sending data
        
        Sends data after it's passed through outgoing()
        """
        resp = self.outgoing(resp)
        if self.verbose:
            print(f"[{self.client_address[0]}:{self.client_address[1]}] {self.proto} data sent.")
        self.send(resp)
        
    def recv(self):
        """Override with protocol/use specific recv method
        
        Use directly to bypass incoming()
        """
        raise NotImplementedError
        
    def incoming(self, data): # Decode recieved data from bytes
        """Process incoming data as it's recieved
        
        Default: Decode and strip incoming data
        """
        try:
            data = data.decode()
        except:
            pass
        return data.strip()
    
    def recv_data(self):
        """Main method to be used for recieving data
        
        Returns data from recv(), after being passed through incoming()
        """
        data = self.incoming(self.recv())
        if data:
            if self.verbose:
                print(f"[{self.client_address[0]}:{self.client_address[1]}] {self.proto} data recieved: {data}")
            return data
        
    def response(self, data):
        """Recieves data processed by incoming(), returns 
        response data to be processed by outgoing()
        
        Called by handle()
        """
        return f"Default {self.proto} response"


class DNSRequestHandler(BaseRequestHandler):
    """RequestHandler class to extend BaseRequestHandler with DNS-specific methods
    
    Declares self.records and self.default_ip
    """
    keepalive=False
    def __init__(self, request, client_address, server):
        self.default_ip = server.default_ip if hasattr(server, "default_ip") else None
        self.records = server.records if hasattr(server, "records") else None
        super().__init__(request, client_address, server)
  
    def incoming(self, data):
        """
        Parses recieved data and returns dnslib.DNSRecord object
        """
        try:
            data = DNSRecord.parse(data)
        except:
            return None
        return data
        
    def outgoing(self, resp):
        """
        Ensure DNS response is packed
        """
        if type(resp) is not bytearray:
            resp = resp.pack()
        return resp

    def response(self, request):
        """
        Passes request to resolve and returns response
        - Main overridable method
        - Returns dnslib.DNSRecord object
        """
        reply = request.reply()
        if self.records:
            reply = self.resolve_from_zone(reply, self.records)            
        if not reply.rr:
            if self.default_ip and (reply.q.qtype == QTYPE.A or reply.q.qtype == QTYPE.AAAA):
                reply.add_answer(RR(str(reply.q.qname), QTYPE.A, rdata=A(self.default_ip), ttl=60))            
            else: # Add other record types here
                reply.header.rcode = RCODE.NXDOMAIN # "Could not be resolved"       
        return reply
        
    def resolve_from_zone(self, request, records): # Maybe fold into Resolver class
        """
        Resolve DNS query using given list of DNS records
        - Return reply with added answers
        """
        qname = request.q.qname
        qtype = QTYPE[request.q.qtype]
        zone = [(rr.rname,QTYPE[rr.rtype],rr) for rr in records]
        for name,rtype,rr in zone:
            if getattr(qname,'__eq__')(name) and (qtype == rtype or qtype == 'ANY' or rtype == 'CNAME'):
                request.add_answer(rr)       
                if rtype in ['CNAME','NS','MX','PTR']:
                    for a_name,a_rtype,a_rr in zone:
                        if a_name == rr.rdata.label and a_rtype in ['A','AAAA']:
                            request.add_ar(a_rr)
        return request 
    
    # Overriding these for logging purposes    
    def recv_data(self):
        """Main method to be used for recieving data
        
        Returns data from recv(), after being passed through incoming()
        """
        return self.incoming(self.recv())
        
    def send_data(self, resp):
        """Main method to be used for sending data
        
        Sends data after it's passed through outgoing()
        """
        if resp.rr and self.verbose:
           print(f"[{self.client_address[0]}:{self.client_address[1]}] Query/response: {QTYPE[resp.q.qtype]} {resp.q.qname} -> {resp.get_a().rdata}")  
        self.send(self.outgoing(resp))

""" RequestHandler and Server Classes
- RequestHandler classes can be subclasses and passed to Server class
- Servers accept RequestHandlers upon initialization
- All servers threading capable
"""

# UDP #

class TCPServer(ThreadedBaseServer, socketserver.TCPServer):
    """Threaded TCP server class, TLS/SSL compatible
    
    Listens for and accepts requests from remote TCP clients,
    passes requests to given RequestHandler class.
    """
    proto = "TCP"
    def __init__(self, server_address, RequestHandlerClass):
        """Constructor.  May be extended, do not override."""
        ThreadedBaseServer.__init__(self, server_address, RequestHandlerClass)
        self.socket = socket.socket(self.address_family, self.socket_type)
                
    def enable_ssl(self, context):
        """Enable TLS/SSL on server socket
        
        :param context: SSLContext to wrap socket with (required)
        :rtype: bool
        """
        try:
            self.socket = context.wrap_socket(self.socket, server_side=True)
        except Exception as e:
            print("TLS/SSL failed.")
            raise e
        self.proto = f"{self.proto} (SSL)"
        return True


class TCPHandler(BaseRequestHandler):
    """Handler class for TCP server connections/requests
    
    Overridable methods:
    - incoming
    - outgoing
    - response
    """
    def send(self, data):
        """Protocol specific method for sending data to remote socket
        
        Called by send_data(), after it passes the data through self.outgoing()
        
        :param data: Data to be sent to remote socket
        """
        self.request.sendall(data)       
        
    def recv(self, buffer: int = 1024):
        """Protocol specific method for recieving data to remote socket
        
        Called by recv_data()
        
        :param buffer: Size of recieve buffer
        :type buffer: int
        :returns data: Data recieved, after being processed through self.incoming()
        """
        return self.request.recv(buffer)


# UDP #

class UDPServer(ThreadedBaseServer, socketserver.UDPServer):
    """Threaded UDP server class 
    
    Extends the functionality of socketserver.UDPServer.
    Passes requests to given RequestHandler class.
    """
    proto = "UDP"
    def __init__(self, server_address, RequestHandlerClass):
        """Constructor.  May be extended, do not override."""
        ThreadedBaseServer.__init__(self, server_address, RequestHandlerClass)
        self.socket = socket.socket(self.address_family, self.socket_type)


class UDPHandler(BaseRequestHandler):
    """Handler class for UDP server requests
    
    Overridable methods:
    - incoming
    - outgoing
    - response
    """
    keepalive = False
    def send(self, data):
        """Protocol specific method for sending data to remote socket
        
        Called by send_data(), after it passes the data through self.outgoing()
        
        :param data: Data to be sent to remote socket
        """
        self.request[1].sendto(data, self.client_address)
        
    def recv(self):
        """Protocol specific method for recieving data to remote socket
        
        Called by recv_data(), which passes the returned data through self.incoming()
        
        :returns data: Data recieved from remote socket
        """
        return self.request[0].strip()


# DNS #

class DNSServerTCP(TCPServer):
    """ Threaded DNS Server (TCP)
    
    Subclass of omniserver.servers.TCPServer that declares self.default_ip and self.record,
    which are needed for resolving incoming queries.Inherits DNS-specific functions from 
    omniserver.servers.BaseDNSServer, general server functions from omniserver.servers.TCPServer
    """
    proto = "DNS (TCP)"
    def __init__(self, server_address, RequestHandlerClass, default_ip=None):
        super().__init__(server_address, RequestHandlerClass)
        self.default_ip = default_ip
        self.records = []  
         
    def add_record(self, zone_record):
        """Add zone-style record to compare incoming queries against
        
        Ex: "google.com 60 IN A 192.168.100.1"
        
        :param zone_record: DNS zone record string to add to server's 'record'
        :type zone_record: str
        """
        self.records.append(*RR.fromZone(zone_record))
        
    def add_zonefile(self, zonefile):
        """Add all DNS records from given DNS zone file
        
        :param zonefile: Path to file containing zone records
        :type zonefile: str
        """
        with open(zonefile) as file:
            rrs = RR.fromZone(file)
            for rr in rrs:
                self.records.append(rr)


class DNSHandlerTCP(DNSRequestHandler):
    """Handler class for DNS server requests (TCP)
     
    Must be used to exchange information larger than 512 bytes.
    DNSRequestMixIn overrides incoming(), outgoing(), and response(). 
    response() can be further overriden to customize DNS resolution method. 
    self.records and self.default_ip inherited from DNSBaseHandler
    """
    def recv(self):
        """Protocol specific method for recieving data to remote socket
        
        Called by recv_data(), which passes the returned data through self.incoming()
        
        :returns data: Data recieved from remote socket
        """
        data = self.request.recv(8192).strip()
        sz = struct.unpack('>H', data[:2])[0]
        if sz < len(data) - 2:
            raise Exception("Wrong size of TCP packet")
        elif sz > len(data) - 2:
            raise Exception("Too big TCP packet")
        return data[2:]

    def send(self, data):
        """Protocol specific method for sending data to remote socket
        
        Called by send_data(), after it passes the data through self.outgoing()
        
        :param data: Data to be sent to remote socket
        """
        sz = struct.pack('>H', len(data))
        self.request.sendall(sz + data)


class DNSServer(UDPServer):
    """Threaded DNS Server (UDP)
    
    Subclass of omniserver.servers.UDPServer that declares self.default_ip and self.record,
    which are needed for resolving incoming queries.Inherits DNS-specific functions from 
    omniserver.servers.BaseDNSServer, general server functions from omniserver.servers.UDPServer
    """
    proto = "DNS"
    def __init__(self, server_address, RequestHandlerClass, default_ip=None):
        super().__init__(server_address, RequestHandlerClass)
        self.default_ip = default_ip
        self.records = []
         
    def add_record(self, zone_record):
        """Add zone-style record to compare incoming queries against
        
        Ex: "google.com 60 IN A 192.168.100.1"
        
        :param zone_record: DNS zone record string to add to server's 'record'
        :type zone_record: str
        """
        self.records.append(*RR.fromZone(zone_record))
        
    def add_zonefile(self, zonefile):
        """Add all DNS records from given DNS zone file
        
        :param zonefile: Path to file containing zone records
        :type zonefile: str
        """
        with open(zonefile) as file:
            rrs = RR.fromZone(file)
            for rr in rrs:
                self.records.append(rr)


class DNSHandler(DNSRequestHandler):
    """Handler class for DNS server requests (UDP)
     
    DNSRequestMixIn overrides incoming(), outgoing(), and response(). 
    response() can be further overriden to customize DNS resolution method. 
    self.records and self.default_ip inherited from DNSBaseHandler
    """        
    def recv(self):
        """Protocol specific method for recieving data to remote socket
        
        Called by recv_data(), which passes the returned data through self.incoming()
        
        :returns data: Data recieved from remote socket
        """
        return self.request[0].strip()
        
    def send(self, data):
        """Protocol specific method for sending data to remote socket
        
        Called by send_data(), after it passes the data through self.outgoing()
        
        :param data: Data to be sent to remote socket
        """
        self.request[1].sendto(data, self.client_address)


# HTTP #

class HTTPServer(TCPServer):
    """Threaded HTTP server
    
    Subclass of omniserver.servers.TCPServer, works basically the same as http.server.
    TLS/SSL compatible.
    """
    proto = "HTTP"
    server_version = "OmniHTTP/" + __version__
    def __init__(self, server_address, RequestHandlerClass, dir=None):
        super().__init__(server_address, RequestHandlerClass)
        self.working_dir = os.getcwd() if dir is None else dir
        
    def __str__(self):
        return f"{self.proto} Server {self.proto.lower()}://{self.server_address[0]}:{self.server_address[1]}/"
        
    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, directory=self.working_dir)
        
    def enable_ssl(self, context):
        if super().enable_ssl(context):
            self.proto = "HTTPS"
            return True
        return False


class HTTPHandler(SimpleHTTPRequestHandler):
    """Handler class for HTTP/S server connections/requests
    
    """
    def log_message(self, format, *args):
        """Log arbitrary message

        Overriding BaseHTTPRequestHandler to keep
        all Omniserver logs in the same basic style.
        """
        message = format % args
        print(f"[{self.client_address[0]}:{self.client_address[1]}] {message}")
    
    

""" Server Management
- Classes and functions for starting, stoping, and waiting on threaded servers
- Newly created server objects are appended to the init_servers list,
    so they can be started, stopped, or waited on all at once
    
TODO:
    - Make ServerManager class more comprehensive as a wrapper
        - https://stackoverflow.com/questions/9057669/how-can-i-intercept-calls-to-pythons-magic-methods-in-new-style-classes/9059858#9059858
"""
init_servers = [] # All initialized servers
active_servers = [] # Servers that have been started with start() or start_all()

class ServerManager:
    """Wrapper class for ThreadedServer objects
    
    Contains methods for starting and stopping threads,
    subclasses include more protocol-specific methods.
    """ 
    def __init__(self, ServerClass):
        self.server = ServerClass
        init_servers.append(self)
        self.thread = None
        
    def __str__(self):
        return str(self.server)
        
    def __getattr__(self, attr):
        """Provides proxy access to the server objects functions/attributes
        """
        return getattr(self.server, attr)
    
    def start(self, daemon=True):
        """Create and start server process thread (non-blocking)
        
        :param daemon: Daemonize thread
        :type daemon: bool
        """
        if self.thread is not None: # Do nothing if thread has already been started
            return
        self.server.activate()
        active_servers.append(self)
        
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=daemon)
        self.thread.start() # Thread object available for whatever
        return self # Returning self so wait() method can be used on same line
            
    def wait(self, interrupt=KeyboardInterrupt):
        """Wait (block) for server thread, shutdown upon interrupt
        
        :param interrupt: Exception to trigger the shutdown of active thread
        """
        if self.thread is None: # Do nothing if no thread has been started
            return
        print("(Ctrl-C to exit)\n")
        try:
            while 1:
                sleep(1)
                sys.stderr.flush()
                sys.stdout.flush()
        except interrupt:
            pass
        finally:
            self.stop()
            
    def stop(self):
        """Shutdown/close server
        """
        self.server.shutdown()
        active_servers.remove(self)
        self.thread = None


"""Functions for controlling all active servers
"""

def stop_all():
    """Shutdown all currently active server threads
    """
    if len(active_servers) > 0:
        for server in active_servers:
            server.stop()

def wait_all(interrupt=KeyboardInterrupt): # Might replace with signals
    """ Wait indefinetly to allow all non-blocking threads to operate
    
    Shutdown all servers upon triggering interrupt
    
    :param interrupt: Exception to trigger the shutdown of all active threads
    """
    print("(Ctrl-C to exit)\n")
    if len(active_servers) <= 0: # Don't wait if no servers are started
        return
    try:
        while 1:
            sleep(1)
            sys.stderr.flush()
            sys.stdout.flush()
    except interrupt:
        pass
    finally:
        stop_all()

def start_all(wait=True):
    """Start all currently initialized server threads
    
    :param wait: Wait (block) until interrupt is triggered, then shutdown all active servers
    :type wait: bool
    """
    if len(init_servers) > 0:
        for server in init_servers:
            server.start()
        if wait:
            wait_all()
            
   
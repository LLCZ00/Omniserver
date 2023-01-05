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
import threading
import logging
import sys
from time import sleep
from http.server import SimpleHTTPRequestHandler
from dnslib import DNSRecord,RR,A,RCODE,QTYPE
from omniserver import certs

from omniserver.version import __version__

__all__ = ["TCPHandler", "UDPHandler", "DNSHandlerTCP",
            "DNSHandler", "HTTPHandler"]

"""RequestHandler Base Classes
- Inherited by RequestHandler subclasses in omniserver.servers to provide overridable data handling methods
"""
class BaseRequestHandler(socketserver.BaseRequestHandler):
    """Base class containing overridable methods for handling socket requests, extending socketserver.BaseRequestHandler
    
    Meant to be inherited by TCP/UDP RequestHandler classes, who shall override 
    send() and recv() with their specific implimentations. The send/recv and 
    send_data/recv_data methods are seperated so as to easily allow for bypassing the 
    incoming/outgoing filter methods, if necessary.
    """
    proto = ""
    
    def setup(self):
        """Called by socketserver before handle()
        """
        self.client = f"[{self.client_address[0]}:{self.client_address[1]}]"
        
    def send(self, data):
        """Override with protocol/use specific send method
        
        Use directly to bypass outgoing()
        """
        raise NotImplementedError
        
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
        
    def outgoing(self, resp): # Encode data to be sent
        """Process outgoing response/data before it's sent
        
        Default: encode data and add newline
        """
        if type(resp) is not bytes:
            resp = f"{resp}\n".encode("utf-8")
        return resp
        
    def recv_data(self):
        """Main method to be used for recieving data
        
        Returns data from recv(), after being passed through incoming()
        """
        data = self.incoming(self.recv())
        if data:
            logging.info(f"{self.client} {self.proto} data recieved: {data}")
        return data
        
    def send_data(self, resp):
        """Main method to be used for sending data
        
        Sends data after it's passed through outgoing()
        """
        self.send(self.outgoing(resp))
        logging.info(f"{self.client} Response sent.")
        
    def response(self, data):
        """Return response to be sent to client
        
        Called by handle()
        """
        return f"Default {self.proto} response"


""" RequestHandler and Server Classes
- RequestHandler classes can be subclasses and passed to Server class
- Servers accept RequestHandlers upon initialization
- All servers threading capable
"""

# UDP #

class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP server class 
    
    Extends the functionality of socketserver.TCPServer.
    Passes requests to given RequestHandler class.
    TLS/SSL compatible.
    """
    allow_reuse_address = True
    proto = "TCP"
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate=False)
        
    def __str__(self):
        server_addr = self.socket.getsockname()
        return f"{self.proto} Server {server_addr[0]}:{server_addr[1]}"
        
    def bind_and_activate(self):
        """Bind socket and activate the server
        """
        try:
            self.server_bind()
            self.server_activate()
        except:
            self.server_close()
            logging.error(f"Binding/activation failed")
            raise
        logging.info(f"[OMNI] Started {self}")
            
    def enable_ssl(self, context):
        """Enable TLS/SSL on server socket
        
        :param context: SSLContext to wrap socket with (required)
        :rtype: bool
        """
        try:
            self.socket = context.wrap_socket(self.socket, server_side=True)
        except Exception as e:
            logging.exception("TLS/SSL failed.")
            raise e
        self.proto = f"{self.proto} (SSL)"
        return True
        
    def shutdown(self):
        """Stops serve_forever loop
        """
        super().shutdown()
        logging.info(f"[OMNI] {self} closed.")


class TCPHandler(BaseRequestHandler):
    """Handler class for TCP server connections/requests
    """
    proto="TCP"
    
    def setup(self):
        """Called by socketserver before handle()
        """
        self.client = f"[{self.client_address[0]}:{self.client_address[1]}]"
        logging.info(f"{self.client} {self.proto} connection established.")        
        
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

    def handle(self):
        """Called by socketserver upon connection/request
        """        
        try:
            while True:
                data = self.recv_data()
                if not data:
                    break   
                response = self.response(data)
                self.send_data(response)               
        except Exception as e:
            logging.exception(f"Exception occured within {self.proto} server")            
        
    def finish(self):
        """socketserver.BaseRequestHandler.finish(), called after handle()
        """
        logging.info(f"{self.client} Connection closed.")


# UDP #

class UDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    """Threaded UDP server class 
    
    Extends the functionality of socketserver.UDPServer.
    Passes requests to given RequestHandler class.
    """
    allow_reuse_address = True
    proto = "UDP"
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate=False)
        
    def __str__(self):
        server_addr = self.socket.getsockname()
        return f"{self.proto} Server {server_addr[0]}:{server_addr[1]}"
        
    def bind_and_activate(self):
        """Bind socket and activate the server
        """
        try:
            self.server_bind()
            self.server_activate()
        except:
            self.server_close()
            logging.error(f"Binding/activation failed")
            raise
        logging.info(f"[OMNI] Started {self}")

    def shutdown(self):
        """Stops serve_forever loop
        """
        super().shutdown()
        logging.info(f"[OMNI] {self} closed.")


class UDPHandler(BaseRequestHandler):
    """Handler class for UDP server requests
    """
    proto = "UDP"
    
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
        
    def handle(self):
        """Called by socketserver upon recieving UDP data
        """
        try:
            data = self.recv_data()
            if data:
                response = self.response(data)
                self.send_data(response)                
        except Exception as e:
            logging.exception(f"Exception occured within {self.proto} server")


# DNS #

class BaseDNSServer:
    """MixIn class with DNS-specific methods to extend TCP/UDP ServerClasses
    """
    def set_default_ip(self, ip):
        """Set default IP for unresolved A record queries
        
        :param ip: IP address
        :type ip: str
        """
        self.default_ip = ip
         
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


class DNSRequestMixIn:
    """MixIn class to extend BaseRequestHandler TCP or UDP subclasses with DNS-specific methods
    
    Declares self.records and self.default_ip
    """
    def setup(self):
        """
        Called by socketserver before handle()
        - Do not override
        """
        self.client = f"[{self.client_address[0]}:{self.client_address[1]}]"
        self.records = self.server.records
        self.default_ip = self.server.default_ip
        
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
        
    def default(self, reply):
        """
        Default action if DNS query fails to resolve
        - Returns dnslib.DNSRecord object
        """
        if self.default_ip and (reply.q.qtype == QTYPE.A or reply.q.qtype == QTYPE.AAAA):
            reply.add_answer(RR(str(reply.q.qname), QTYPE.A, rdata=A(self.default_ip), ttl=60))            
        else: # Add other record types here
            reply.header.rcode = RCODE.NXDOMAIN # "Could not be resolved"
        return reply

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
            reply = self.default(reply)        
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
        if resp.rr:
           logging.info(f"{self.client} Query/response: {QTYPE[resp.q.qtype]} {resp.q.qname} -> {resp.get_a().rdata}")  
        self.send(self.outgoing(resp))



class DNSServerTCP(TCPServer, BaseDNSServer):
    """ Threaded DNS Server (TCP)
    
    Subclass of omniserver.servers.TCPServer that declares self.default_ip and self.record,
    which are needed for resolving incoming queries.Inherits DNS-specific functions from 
    omniserver.servers.BaseDNSServer, general server functions from omniserver.servers.TCPServer
    """
    proto = "DNS (TCP)"
    def __init__(self, server_address, RequestHandlerClass, default_ip: str = None):
        super().__init__(server_address, RequestHandlerClass)
        self.default_ip = default_ip
        self.records = []


class DNSHandlerTCP(DNSRequestMixIn, TCPHandler):
    """Handler class for DNS server requests (TCP)
     
    Must be used to exchange information larger than 512 bytes.
    DNSRequestMixIn overrides incoming(), outgoing(), and response(). 
    response() can be further overriden to customize DNS resolution method. 
    self.records and self.default_ip inherited from DNSBaseHandler
    """
    proto = "DNS (TCP)"
    
    def recv(self):
        data = self.request.recv(8192).strip()
        sz = struct.unpack('>H', data[:2])[0]
        if sz < len(data) - 2:
            raise Exception("Wrong size of TCP packet")
        elif sz > len(data) - 2:
            raise Exception("Too big TCP packet")
        return data[2:]

    def send(self, resp):
        sz = struct.pack('>H', len(data))
        self.request.sendall(sz + data)


class DNSServer(UDPServer, BaseDNSServer):
    """Threaded DNS Server (UDP)
    
    Subclass of omniserver.servers.UDPServer that declares self.default_ip and self.record,
    which are needed for resolving incoming queries.Inherits DNS-specific functions from 
    omniserver.servers.BaseDNSServer, general server functions from omniserver.servers.UDPServer
    """
    proto = "DNS"
    def __init__(self, server_address, RequestHandlerClass, default_ip: str = None):
        super().__init__(server_address, RequestHandlerClass)
        self.default_ip = default_ip
        self.records = []


class DNSHandler(DNSRequestMixIn, UDPHandler):
    """Handler class for DNS server requests (UDP)
     
    DNSRequestMixIn overrides incoming(), outgoing(), and response(). 
    response() can be further overriden to customize DNS resolution method. 
    self.records and self.default_ip inherited from DNSBaseHandler
    """
    proto = "DNS"
    def recv(self):
        return self.request[0].strip()
        
    def send(self, data):
        self.request[1].sendto(data, self.client_address)


# HTTP #

class HTTPServer(TCPServer):
    """Threaded HTTP server
    
    Subclass of omniserver.servers.TCPServer, works basically the same as http.server.
    TLS/SSL compatible.
    """
    proto = "HTTP"
    def __init__(self, server_address, RequestHandlerClass, dir: str = None):
        super().__init__(server_address, RequestHandlerClass)
        self.working_dir = dir
        
    def __str__(self):
        server_addr = self.socket.getsockname()
        return f"{self.proto} Server {self.proto.lower()}://{server_addr[0]}:{server_addr[1]}/"
        
    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, directory=self.working_dir)
        
    def enable_ssl(self, context):
        if super().enable_ssl(context):
            self.proto = "HTTPS"


class HTTPHandler(SimpleHTTPRequestHandler):
    """Handler class for HTTP/S server requests
    
    Basic subclass of http.server.SimpleHTTPRequestHandler
    """
    server_version = "OmniHTTP/" + __version__
    proto = "HTTP"
    
    def log_message(self, format, *args):
        """Log arbitrary message
        
        Overriding BaseHTTPRequestHandler to keep
        all Omniserver logs in the same basic style.
        """
        message = format % args
        logging.info(f"[{self.client_address[0]}:{self.client_address[1]}] {message}")
    
    

""" Server Management
- Classes and functions for starting, stoping, and waiting on threaded servers
- Newly created server objects are appended to the active_servers list,
    so they can all be started or stopped at once
"""
active_servers = [] 

class ServerManager:
    """Wrapper class for ThreadedServer objects
    
    Contains methods for starting and stopping threads,
    subclasses include more protocol-specific methods.
    """ 
    def __init__(self, ServerClass):
        self.server = ServerClass
        active_servers.append(self)
    
    def start(self, thread=True, daemon=True):
        """Create and start server process (blocking) or thread (non-blocking, default)
        
        :param thread: Start server in its own thread (Non-blocking)
        :type thread: bool
        :param daemon: Daemonize thread
        :type daemon: bool
        """
        self.server.bind_and_activate()

        if thread:
            server_thread = threading.Thread(target=self.server.serve_forever, daemon=daemon)
            server_thread.start()            
        else:
            try:
                print("(Ctrl-C to exit)\n") # Won't print if below
                self.server.serve_forever()                
            except KeyboardInterrupt:
                pass
            finally:
                self.stop()                
        return self # Returning self so wait() method can be used on same line
            
    def wait(self):
        """Wait (block) for server thread, shutdown upon interrupt
        """
        print("(Ctrl-C to exit)\n")
        try:
            while 1:
                sleep(1)
                sys.stderr.flush()
                sys.stdout.flush()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
            
    def stop(self):
        """Shutdown/close server
        """
        self.server.shutdown()
        active_servers.remove(self)


class TCPServerManager(ServerManager):
    """ServerManager extended with TCP specific functions
    """
    def enable_ssl(self, context):
        return self.server.enable_ssl(context)

class DNSServerManager(ServerManager):
    """ServerManager extended with DNS specific wrapper functions
    """

    def add_record(self, *records: str):
        """Add zone-style record to compare incoming queries against
        
        Ex: "google.com 60 IN A 192.168.100.1"
        
        :param zone_record: DNS zone record string to add to server's 'record'
        :type zone_record: str
        """
        for record in records:
            self.server.add_record(record)
        
    def add_zonefile(self, zonefile: str):
        """Add all DNS records from given DNS zone file
        
        :param zonefile: Path to file containing zone records
        :type zonefile: str
        """
        self.server.add_zonefile(zonefile)
        
    def set_default_ip(self, ip):
        """Set default IP for unresolved A record queries
        
        :param ip: IP address
        :type ip: str
        """
        self.server.default_ip = ip


"""Functions for controlling all active servers
"""

def stop_all():
    """Shutdown all currently active server threads
    """
    if len(active_servers) == 0:
        return
    while len(active_servers) != 0:
        for server in active_servers: # Makin sure all them things close
            server.stop()
    logging.info("[OMNI] All servers shut down.")    

def wait_all(interrupt=KeyboardInterrupt): # Might replace with signals
    """ Wait indefinetly to allow all non-blocking threads to operate
    
    Shutdown all servers upon triggering interrupt
    
    :param interrupt: Exception to trigger the shutdown of all active threads
    :param stop: 
    """
    print("(Ctrl-C to exit)\n")
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
    if len(active_servers) > 0:
        for server in active_servers:
            server.start()
        if wait:
            wait_all()
            
   